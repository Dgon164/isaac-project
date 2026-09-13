// bench.go -- walk/bed.py compiled. same store, same walk, same score,
// same answers; Go instead of Python, goroutines instead of processes.
//
//     go build -o walk/go/bench.exe ./walk/go        (once, ~1s)
//     walk/go/bench.exe 999999 -jobs 24               the whole of squad
//     walk/go/bench.exe 999999                        one core
//
// Reads ISAAC_SQUAD (or the Downloads path) and walk/tools.json (his
// thesaurus + his kinds table), exactly what bed.py loads by default.
// Totals must equal bed.py's to the question; if they drift, the port
// is wrong, not the machine.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
	"unicode/utf8"
)

// ------------------------------------------------------------ linker.py
var STOP = map[string]bool{}

func init() {
	for _, w := range strings.Fields("the a an of to in and or is are was were be been it its this that these those for with as at by on from but if so than then too very can will would should could may might not no yes you i we they he she them their our your my me us him her do does did have has had which who what when where why how about into over under out up down off just also only more most some any all each every both either neither such same other another much many few less least") {
		STOP[w] = true
	}
}

// python's str.lower() uses the full case mapping: the one unconditional
// difference from Go's simple mapping is U+0130 (Turkish dotted I), which
// python turns into "i" + combining dot. Without this, "İzmir" becomes
// the term "izmir" here and "zmir" there.
func lower(s string) string {
	if strings.Contains(s, "İ") {
		s = strings.ReplaceAll(s, "İ", "i̇")
	}
	return strings.ToLower(s)
}

var termRe = regexp.MustCompile(`[a-z][a-z0-9_\-]*`)

func terms(s string) []string {
	toks := termRe.FindAllString(lower(s), -1)
	out := make([]string, 0, len(toks))
	for _, t := range toks {
		t = strings.ReplaceAll(t, "-", "_")
		if STOP[t] || len(t) < 3 {
			continue
		}
		out = append(out, t)
	}
	return out
}

// re.split(r"(?<=[.!?])\s+|\n+", text) without lookbehind: a whitespace
// run right after . ! ? splits, and so does any run of newlines. python
// strips each piece and drops the empty ones before numbering them.
func sentences(text string) []string {
	rs := []rune(text)
	var out []string
	var cur []rune
	flush := func() {
		s := strings.TrimFunc(string(cur), unicode.IsSpace)
		if s != "" {
			out = append(out, s)
		}
		cur = cur[:0]
	}
	for i := 0; i < len(rs); {
		c := rs[i]
		if unicode.IsSpace(c) && i > 0 && (rs[i-1] == '.' || rs[i-1] == '!' || rs[i-1] == '?') {
			for i < len(rs) && unicode.IsSpace(rs[i]) {
				i++
			}
			flush()
			continue
		}
		if c == '\n' {
			for i < len(rs) && rs[i] == '\n' {
				i++
			}
			flush()
			continue
		}
		cur = append(cur, c)
		i++
	}
	flush()
	return out
}

// ------------------------------------------------------------ core.py
// one store per article. items are numbered; a name looks its number up.
type Store struct {
	id      map[string]int32
	names   []string
	isSent  []bool
	content []string
	refs    [][]int32
	feat    []uint8 // bit0 computed; then year number name percent money
}

func newStore() *Store { return &Store{id: map[string]int32{}} }

func (s *Store) add(name string, sent bool) int32 {
	n := int32(len(s.names))
	s.id[name] = n
	s.names = append(s.names, name)
	s.isSent = append(s.isSent, sent)
	s.content = append(s.content, "")
	s.refs = append(s.refs, nil)
	s.feat = append(s.feat, 0)
	return n
}

func has(xs []int32, x int32) bool {
	for _, y := range xs {
		if y == x {
			return true
		}
	}
	return false
}

func link(text string, s *Store) {
	for i, sent := range sentences(text) {
		ts := terms(sent)
		if len(ts) == 0 {
			continue
		}
		k := len(ts)
		if k > 3 {
			k = 3
		}
		name := fmt.Sprintf("s%03d_%s", i, strings.Join(ts[:k], "_"))
		sid, ok := s.id[name]
		if !ok {
			sid = s.add(name, true)
		}
		s.isSent[sid] = true // a name clash overwrites the item, as in python
		s.content[sid] = sent
		s.feat[sid] = 0
		trefs := make([]int32, len(ts))
		for j, t := range ts {
			tid, ok := s.id[t]
			if !ok {
				tid = s.add(t, false)
				s.refs[tid] = []int32{sid}
			} else if !has(s.refs[tid], sid) {
				s.refs[tid] = append(s.refs[tid], sid)
			}
			trefs[j] = tid
		}
		s.refs[sid] = trefs
	}
}

// ------------------------------------------------------------ mind.py
// one entry of a kinds row: the feature's bit and its log odds. rows keep
// the file's key order because python sums them in that order and the
// sum is rounded to two places -- order changes the last bit.
type weight struct {
	bit uint8
	w   float64
}

var (
	SYN       map[string][]string
	KINDS     map[string][]weight
	FEATS     = []string{"year", "number", "name", "percent", "money"}
	KINDWORDS = []string{"who", "when", "where", "how many", "how much", "how", "what", "which", "why"}
	yearRe    = regexp.MustCompile(`\b(1[0-9]{3}|20[0-9]{2})\b`)
	digitRe   = regexp.MustCompile(`[0-9]`)
	nameRe    = regexp.MustCompile(`\b[A-Z][a-z]+`)
	moneyRe   = regexp.MustCompile(`[$\x{00a3}\x{20ac}]|\bmillion\b|\bbillion\b`)
)

func kind(q string) string {
	q = strings.TrimFunc(lower(q), unicode.IsSpace)
	head := q
	if rs := []rune(q); len(rs) > 40 {
		head = string(rs[:40])
	}
	for _, k := range KINDWORDS {
		if strings.HasPrefix(q, k) || strings.Contains(head, " "+k+" ") {
			return k
		}
	}
	return "other"
}

func (s *Store) feats(n int32) uint8 {
	f := s.feat[n]
	if f&1 != 0 {
		return f
	}
	t := s.content[n]
	f = 1
	if yearRe.MatchString(t) {
		f |= 2
	}
	if digitRe.MatchString(t) {
		f |= 4
	}
	rest := t
	if t != "" {
		_, sz := utf8.DecodeRuneInString(t)
		rest = t[sz:]
	}
	if nameRe.MatchString(rest) {
		f |= 8
	}
	if strings.Contains(t, "%") || strings.Contains(lower(t), "percent") {
		f |= 16
	}
	if moneyRe.MatchString(t) {
		f |= 32
	}
	s.feat[n] = f
	return f
}

func round2(x float64) float64 {
	v, _ := strconv.ParseFloat(strconv.FormatFloat(x, 'f', 2, 64), 64)
	return v
}

// one step of python 3.12's sum() over floats: neumaier compensated
// summation. naive adding differs in the last bit and flips ties.
func addc(s, c, x float64) (float64, float64) {
	t := s + x
	if math.Abs(s) >= math.Abs(x) {
		c += (s - t) + x
	} else {
		c += (x - t) + s
	}
	return t, c
}

type cand struct {
	own  int
	rare float64
	fit  float64
	bagc int
	n    int32
}

// python: cands.sort(reverse=True) over ((own, rare, fit, bag), name)
func better(a, b cand, s *Store) bool {
	if a.own != b.own {
		return a.own > b.own
	}
	if a.rare != b.rare {
		return a.rare > b.rare
	}
	if a.fit != b.fit {
		return a.fit > b.fit
	}
	if a.bagc != b.bagc {
		return a.bagc > b.bagc
	}
	return s.names[a.n] > s.names[b.n]
}

// per-worker scratch: stamp arrays instead of fresh sets per question
type scratch struct {
	seen, own, bag, dup []int32
	stamp               int32
	queue, ownIds       []int32
	top                 []cand
}

func (w *scratch) size(n int) {
	if len(w.seen) < n {
		w.seen = make([]int32, n)
		w.own = make([]int32, n)
		w.bag = make([]int32, n)
		w.dup = make([]int32, n)
		w.stamp = 0
	}
}

// the top three of score_all; nil when nothing in the bag is in the store
func ask(s *Store, q string, w *scratch) []cand {
	w.size(len(s.names))
	w.stamp++
	st := w.stamp
	w.queue = w.queue[:0]
	w.ownIds = w.ownIds[:0]
	for _, t := range terms(q) {
		if id, ok := s.id[t]; ok {
			if w.own[id] != st {
				w.own[id] = st
				w.ownIds = append(w.ownIds, id)
			}
			if w.bag[id] != st {
				w.bag[id] = st
				w.queue = append(w.queue, id)
			}
		}
		for _, y := range SYN[t] {
			if id, ok := s.id[y]; ok && w.bag[id] != st {
				w.bag[id] = st
				w.queue = append(w.queue, id)
			}
		}
	}
	if len(w.queue) == 0 {
		return nil
	}
	// the walk: depth one per step, nothing pulled twice
	for _, id := range w.queue {
		w.seen[id] = st
	}
	for i := 0; i < len(w.queue); i++ {
		for _, r := range s.refs[w.queue[i]] {
			if w.seen[r] != st {
				w.seen[r] = st
				w.queue = append(w.queue, r)
			}
		}
	}
	row := KINDS[kind(q)]
	w.top = w.top[:0]
	for _, n := range w.queue {
		if !s.isSent[n] {
			continue
		}
		c := cand{n: n}
		for _, t := range s.refs[n] { // a sentence's refs carry repeats
			if w.dup[t] == st {
				continue
			}
			w.dup[t] = st
			if w.bag[t] == st {
				c.bagc++
				if w.own[t] == st {
					c.own++
				}
			}
		}
		// rarity summed in one fixed order (the question's), so two
		// sentences sharing the same words get the same last bit, as
		// python's set iteration gives them
		rs, rc := 0.0, 0.0
		for _, t := range w.ownIds {
			if w.dup[t] == st {
				rs, rc = addc(rs, rc, 1.0/float64(len(s.refs[t])))
			}
		}
		c.rare = rs + rc
		for _, t := range s.refs[n] {
			w.dup[t] = 0
		}
		if c.bagc == 0 {
			continue // shares nothing with the bag: a tangent
		}
		if row != nil {
			f := s.feats(n)
			fs, fc := 0.0, 0.0
			for _, kw := range row {
				if f&kw.bit != 0 {
					fs, fc = addc(fs, fc, kw.w)
				}
			}
			c.fit = round2(fs + fc)
		}
		pos := len(w.top) // keep the best three
		for pos > 0 && better(c, w.top[pos-1], s) {
			pos--
		}
		if pos < 3 {
			if len(w.top) < 3 {
				w.top = append(w.top, cand{})
			}
			copy(w.top[pos+1:], w.top[pos:len(w.top)-1])
			w.top[pos] = c
		}
	}
	return w.top
}

// ------------------------------------------------------------ bed.py
type QA struct {
	Question     string `json:"question"`
	IsImpossible bool   `json:"is_impossible"`
	Answers      []struct {
		Text string `json:"text"`
	} `json:"answers"`
}
type Para struct {
	Context string `json:"context"`
	QAs     []QA   `json:"qas"`
}
type Article struct {
	Title      string `json:"title"`
	Paragraphs []Para `json:"paragraphs"`
}

type result struct{ asked, top1, top3, nothing int }

var dump *os.File // -dump FILE: one line per question, the winner and its score (serial only)

func work(art *Article, w *scratch) result {
	s := newStore()
	for _, p := range art.Paragraphs {
		link(p.Context, s)
	}
	var r result
	for _, p := range art.Paragraphs {
		for _, qa := range p.QAs {
			key := lower(qa.Answers[0].Text)
			top := ask(s, qa.Question, w)
			r.asked++
			if dump != nil {
				if len(top) == 0 {
					fmt.Fprintf(dump, "%s\t%s\t-\n", art.Title, qa.Question)
				} else {
					c := top[0]
					fmt.Fprintf(dump, "%s\t%s\t%s\t%d\t%.6f\t%.2f\t%d\n", art.Title, qa.Question,
						s.names[c.n], c.own, c.rare, c.fit, c.bagc)
				}
			}
			if len(top) == 0 {
				r.nothing++
				continue
			}
			if strings.Contains(lower(s.content[top[0].n]), key) {
				r.top1++
				r.top3++
				continue
			}
			for _, c := range top[1:] {
				if strings.Contains(lower(s.content[c.n]), key) {
					r.top3++
					break
				}
			}
		}
	}
	return r
}

func findTools() string {
	if p := os.Getenv("ISAAC_TOOLS"); p != "" {
		return p
	}
	for _, p := range []string{"walk/tools.json", "tools.json", "../tools.json"} {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	exe, _ := os.Executable()
	return filepath.Join(filepath.Dir(exe), "..", "tools.json")
}

func main() {
	want := 500
	jobs := 1
	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-jobs" && i+1 < len(os.Args) {
			jobs, _ = strconv.Atoi(os.Args[i+1])
			i++
		} else if os.Args[i] == "-dump" && i+1 < len(os.Args) {
			dump, _ = os.Create(os.Args[i+1])
			jobs = 1
			i++
		} else if v, err := strconv.Atoi(os.Args[i]); err == nil {
			want = v
		}
	}
	squad := os.Getenv("ISAAC_SQUAD")
	if squad == "" {
		squad = `C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json`
	}
	tload := time.Now()
	raw, err := os.ReadFile(squad)
	if err != nil {
		fmt.Println("no squad:", err)
		os.Exit(1)
	}
	var data struct {
		Data []Article `json:"data"`
	}
	if err := json.Unmarshal(raw, &data); err != nil {
		fmt.Println("bad squad:", err)
		os.Exit(1)
	}
	var tools struct {
		Thesaurus map[string][]string        `json:"thesaurus"`
		Kinds     map[string]json.RawMessage `json:"kinds"`
	}
	tp := findTools()
	if raw, err := os.ReadFile(tp); err == nil {
		json.Unmarshal(raw, &tools)
	} else {
		fmt.Println("no tools.json found (bed.py would fall back to wordnet) --", err)
	}
	SYN = tools.Thesaurus
	KINDS = map[string][]weight{}
	for k, raw := range tools.Kinds { // keep each row's key order
		dec := json.NewDecoder(bytes.NewReader(raw))
		dec.Token()
		var row []weight
		for dec.More() {
			t, _ := dec.Token()
			var w float64
			dec.Decode(&w)
			for i, fn := range FEATS {
				if fn == t.(string) {
					row = append(row, weight{1 << uint(i+1), w})
				}
			}
		}
		KINDS[k] = row
	}

	// the same cut bed.py makes
	var arts []*Article
	n := 0
	for ai := range data.Data {
		if n >= want {
			break
		}
		art := &data.Data[ai]
		take := &Article{Title: art.Title}
		for _, p := range art.Paragraphs {
			var qas []QA
			for _, qa := range p.QAs {
				if qa.IsImpossible || len(qas) >= want-n {
					continue
				}
				qas = append(qas, qa)
			}
			n += len(qas)
			take.Paragraphs = append(take.Paragraphs, Para{Context: p.Context, QAs: qas})
		}
		arts = append(arts, take)
	}
	fmt.Printf("loaded %d articles, %d questions, %d thesaurus words, kinds for %d, in %.1fs (%s)\n",
		len(arts), n, len(SYN), len(KINDS), time.Since(tload).Seconds(), tp)

	t0 := time.Now()
	results := make([]result, len(arts))
	if jobs > 1 {
		idx := make(chan int, len(arts))
		for i := range arts {
			idx <- i
		}
		close(idx)
		var wg sync.WaitGroup
		for j := 0; j < jobs; j++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				w := &scratch{}
				for i := range idx {
					results[i] = work(arts[i], w)
				}
			}()
		}
		wg.Wait()
	} else {
		w := &scratch{}
		for i, a := range arts {
			results[i] = work(a, w)
		}
	}
	dt := time.Since(t0).Seconds()
	var tot result
	for _, r := range results {
		tot.asked += r.asked
		tot.top1 += r.top1
		tot.top3 += r.top3
		tot.nothing += r.nothing
	}
	fmt.Printf("asked %d   top1 %d (%.1f%%)   top3 %d (%.1f%%)   nothing %d   %.1fs (%.0f q/s, jobs=%d)\n",
		tot.asked, tot.top1, 100.0*float64(tot.top1)/float64(tot.asked),
		tot.top3, 100.0*float64(tot.top3)/float64(tot.asked), tot.nothing,
		dt, float64(tot.asked)/dt, jobs)
}
