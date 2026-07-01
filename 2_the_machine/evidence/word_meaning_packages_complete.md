# Word Meaning Packages — Complete Seed Set (Final)

## Relation Types Reference

IS_A, HAS_PROPERTY, CAN_DO, DID, REQUIRES, CAUSES, REJECTS, PART_OF, 
LOCATED, ACTED_ON, HAS_FEATURE, BEFORE, SIMULTANEOUS_WITH

Comparators: eq, neq, gt, lt, gte, lte
Booleans: TRUE, FALSE

CAUSES and BEFORE are stored as single directional edges. 
Backward traversal yields the inverse reading (CAUSED_BY, AFTER).

---

## Group 1: Articles & Demonstratives

WORD: the
  type:       definite article
  function:   scope marker — identifies a specific known instance, not the category
  attaches:   forward to the next noun phrase
  signals:    singular (unless followed by plural noun), specific known referent,
              both speaker and listener can identify which instance
  result:     marks the following noun as INSTANCE (specific) rather than TYPE (category).
              does not produce a claim on its own — it modifies how the noun's claims fire
  not:        "a/an" (introduces new or nonspecific instance — speaker knows, listener may not),
              "all/every" (category-level — applies to the type, not an instance),
              "this/that" (also specific, but adds spatial/contextual proximity — "the" is neutral)

---

WORD: a
  type:       indefinite article, singular
  function:   instance introducer — signals that a new, nonspecific instance of the
              following noun is entering discourse. the speaker may or may not have
              a particular instance in mind; the listener cannot yet identify which one
  attaches:   forward to the next noun phrase (noun must be singular and countable)
  signals:    singular, nonspecific referent, new-to-discourse. the listener is not
              expected to know which instance. may also signal category membership
              ("a dog is loyal" = any member of the type DOG)
  result:     marks the following noun as INSTANCE (nonspecific) or, in generic usage,
              as TYPE (any representative member). does not produce a claim on its own —
              it sets the referent scope for the noun's downstream claims
  not:        "the" (specific known referent — both parties can identify it.
              "a" introduces, "the" retrieves),
              "an" (identical function, different phonological form — "an" appears
              before vowel sounds. mechanically equivalent to "a"),
              "one" (numeric — emphasizes quantity = 1. "a dog" introduces a dog;
              "one dog" insists on the count being exactly one),
              "some" (indefinite like "a" but plural-compatible and carries a
              partitive sense — "some dogs" vs "a dog")
  notes:      in generic statements ("a triangle has three sides"), "a" scopes over
              the type rather than a specific instance. the system should detect
              generic usage when the predicate is a permanent/defining property
              (HAS_FEATURE, IS_A) rather than a situational one (DID, LOCATED)

---

WORD: an
  type:       indefinite article, singular (vowel-onset variant)
  function:   instance introducer — identical mechanical function to "a". signals
              that a new, nonspecific instance of the following noun is entering
              discourse. the only difference from "a" is phonological: "an" appears
              before words beginning with a vowel sound
  attaches:   forward to the next noun phrase (noun must be singular, countable,
              and begin with a vowel sound)
  signals:    singular, nonspecific referent, new-to-discourse. identical signal
              profile to "a"
  result:     marks the following noun as INSTANCE (nonspecific) or, in generic usage,
              as TYPE. does not produce a claim on its own — modifies the noun's
              referent scope. mechanically identical to "a" after attachment
  not:        "a" (same function, different phonological context — "a" before consonant
              sounds, "an" before vowel sounds. after attachment resolves, they are
              indistinguishable in the processing pipeline),
              "the" (definite — marks known referent. "an" introduces unknown),
              "one" (numeric emphasis on count = 1, not mere introduction)
  notes:      selection depends on the SOUND of the following word, not the spelling.
              "an hour" (silent h), "a university" (starts with /juː/ consonant sound).
              the system should treat "a" and "an" as the same operator after the
              phonological gate is passed

---

WORD: this
  type:       proximal demonstrative determiner, singular
  function:   proximal scope marker — identifies a specific known instance AND signals
              that the referent is near the speaker in space, time, or discourse.
              acts as a strong forward pointer that also carries proximity metadata
  attaches:   forward to the next noun phrase (noun must be singular). can also function
              anaphorically, pointing backward to the most recently introduced referent
              while marking it as the current focus of attention
  signals:    singular, specific known referent, proximal — the referent is close
              (physically near, temporally current, or just mentioned in discourse).
              carries emphasis: "this" actively selects and foregrounds the referent,
              pulling it into focus
  result:     marks the following noun as INSTANCE (specific) + PROXIMAL.
              does not produce a claim on its own — modifies the noun's referent
              scope and adds a proximity/focus layer. downstream claims fire against
              the specific proximal instance
  not:        "the" (also specific and singular, but neutral — carries no proximity
              or emphasis. "the book" retrieves a known book; "this book" retrieves
              a known book AND signals it is near or currently relevant),
              "that" (distal demonstrative — specific known referent but FAR in space,
              time, or discourse. "this" = near, "that" = far),
              "these" (proximal like "this" but plural),
              "it" (neutral backward reference — substitutes without emphasis.
              "this" substitutes WITH emphasis and proximity selection)
  notes:      "this" in discourse-anaphoric use ("I saw a dog. This dog was huge.")
              functions like a definite article with added focus. it upgrades a
              previously introduced referent to foreground status. the system should
              treat discourse-anaphoric "this" as resolving backward to the last
              matching noun, then retagging it as PROXIMAL + FOCUSED

---

WORD: that (determiner)
  type:       distal demonstrative determiner, singular
  function:   distal scope marker — identifies a specific known instance AND signals
              that the referent is far from the speaker in space, time, or discourse.
              acts as a forward pointer with distance metadata. creates separation
              between the speaker and the referent
  attaches:   forward to the next noun phrase (noun must be singular)
  signals:    singular, specific known referent, distal — the referent is far
              (physically distant, temporally past, or mentioned earlier in discourse
              and no longer the current focus). may carry mild emotional distancing
              ("that idea" can signal the speaker is pulling away from it)
  result:     marks the following noun as INSTANCE (specific) + DISTAL.
              does not produce a claim on its own — modifies the noun's referent
              scope and adds a distance layer. downstream claims fire against
              the specific distal instance
  not:        "this" (proximal — near the speaker. "that" = far, "this" = near.
              "this problem" is the one in front of you; "that problem" is the
              one over there or from before),
              "the" (specific but neutral — no distance signal. "the" retrieves;
              "that" retrieves AND marks as distant),
              "that" as relative pronoun (different function entirely — introduces
              a relative clause modifying a noun: "the dog that barked." as a
              determiner, "that" modifies a noun directly: "that dog"),
              "those" (distal like "that" but plural)
  notes:      this package covers ONLY the determiner use of "that" (appearing
              before a noun: "that car", "that idea"). the relative pronoun use
              ("the car that crashed") and the complementizer use ("I know that
              he left") are separate words with different attachment behaviors
              and belong to different packages

---

WORD: these
  type:       proximal demonstrative determiner, plural
  function:   proximal scope marker, plural — identifies a specific known SET of
              instances AND signals that the referents are near the speaker in
              space, time, or discourse. plural counterpart of "this"
  attaches:   forward to the next noun phrase (noun must be plural)
  signals:    plural, specific known referents (multiple), proximal — the referents
              are close (physically near, temporally current, or recently introduced
              in discourse). carries emphasis and active selection, foregrounding
              the entire set
  result:     marks the following noun as INSTANCE_SET (specific, multiple) + PROXIMAL.
              does not produce a claim on its own — modifies the noun's referent
              scope to be plural-specific with proximity. downstream claims fire
              against each member of the resolved set independently.
              "these dogs are big" → dog₁ HAS_PROPERTY big, dog₂ HAS_PROPERTY big, ...
              (claims distribute across the set)
  not:        "those" (distal plural — same structure but marks the set as far.
              "these books" = the ones here/now; "those books" = the ones there/then),
              "the" + plural noun (specific plural but neutral — "the dogs" retrieves
              known dogs without proximity emphasis. "these dogs" retrieves AND
              foregrounds as near),
              "this" (proximal but singular — "this" selects one near instance,
              "these" selects multiple near instances),
              "some" (indefinite plural — does not require the referents to be
              known or specific. "some dogs" = an unspecified subset; "these dogs"
              = a specific known set that is near)

---

WORD: those
  type:       distal demonstrative determiner, plural
  function:   distal scope marker, plural — identifies a specific known SET of
              instances AND signals that the referents are far from the speaker
              in space, time, or discourse. plural counterpart of "that" (determiner)
  attaches:   forward to the next noun phrase (noun must be plural)
  signals:    plural, specific known referents (multiple), distal — the referents
              are far (physically distant, temporally past, or introduced earlier
              in discourse and no longer foregrounded). may carry emotional or
              evaluative distancing ("those people" can signal out-group framing)
  result:     marks the following noun as INSTANCE_SET (specific, multiple) + DISTAL.
              does not produce a claim on its own — modifies the noun's referent
              scope to be plural-specific with distance. downstream claims fire
              against each member of the resolved set independently.
              "those dogs are loud" → dog₁ HAS_PROPERTY loud, dog₂ HAS_PROPERTY loud, ...
              (claims distribute across the set)
  not:        "these" (proximal plural — same structure but marks the set as near.
              "those books" = the ones over there/back then; "these books" = the ones
              right here/right now),
              "the" + plural noun (specific plural but neutral — no distance signal.
              "the dogs" retrieves; "those dogs" retrieves AND marks as distant),
              "that" (distal but singular — "that" selects one far instance,
              "those" selects multiple far instances),
              "them" (object pronoun — substitutes for a known plural referent in
              object position. "those" is a determiner that must precede a noun;
              "them" replaces the noun entirely)
  notes:      "those" can also appear in contrastive constructions without a literal
              spatial meaning: "those who disagree may leave" — here "those" selects
              a subset defined by the following relative clause, functioning closer
              to a pronoun than a determiner. the system should flag this pattern
              when "those" is followed by "who/that/which" rather than a noun

---

## Group 2: Personal Pronouns

WORD: I
  type:       personal pronoun, first person, singular, subject
  function:   self-reference operator — inserts the speaker as the subject
              of the following verb. does not require backward resolution;
              the referent is always the speaker
  attaches:   forward to the next verb. fills the subject slot of that verb's
              claim structure
  signals:    first person, singular, subject case. the speaker is the agent.
              referent is always unambiguous — no resolution search needed
  result:     does not produce a claim on its own. places SPEAKER into the
              subject position so subsequent verbs fire as:
              SPEAKER DID [verb], SPEAKER CAN_DO [verb], etc.
  not:        "me" (same referent but object case — "me" receives the action,
              "I" performs it. "I see the dog" vs "the dog sees me"),
              "my" (possessive — marks ownership by the speaker, not the
              speaker as agent. "I run" vs "my dog"),
              "we" (first person but plural — includes others beyond the speaker)

---

WORD: me
  type:       personal pronoun, first person, singular, object
  function:   self-reference operator, object position — inserts the speaker
              as the target or recipient of a verb or preposition. the speaker
              is acted upon, not acting
  attaches:   backward to the preceding verb or preposition. fills the object
              slot of that element's claim structure
  signals:    first person, singular, object case. the speaker is the patient
              or recipient, not the agent
  result:     does not produce a claim on its own. places SPEAKER into the
              object position so preceding verbs fire as:
              [subject] ACTED_ON SPEAKER, [subject] DID [verb] → target: SPEAKER
  not:        "I" (same referent but subject case — "I" performs, "me" receives),
              "my" (possessive — marks ownership, not object role.
              "give me the book" vs "my book"),
              "myself" (reflexive — used when subject and object are the same
              entity AND the subject is already "I". "me" is the default object
              form; "myself" adds emphasis or reflexivity)

---

WORD: my
  type:       possessive determiner, first person, singular
  function:   ownership marker — binds the following noun to the speaker as
              possessor. operates like a determiner: it occupies the same slot
              as "the" or "a" and also marks the noun as specific
  attaches:   forward to the next noun phrase. claims that noun as belonging
              to or associated with the speaker
  signals:    first person, singular possessor. the noun is a specific known
              instance (like "the"), AND it belongs to the speaker. implies
              definiteness — "my dog" is a known, specific dog
  result:     SPEAKER HAS [noun] or [noun] PART_OF SPEAKER's domain.
              also marks the noun as INSTANCE (specific), not TYPE
  not:        "me" (object pronoun — "me" is acted upon, "my" marks ownership.
              "give me the book" vs "my book"),
              "mine" (possessive pronoun, standalone — "my" must attach to a
              noun, "mine" replaces the noun entirely. "my book" vs "the book
              is mine"),
              "the" (also marks specificity, but without ownership — "the dog"
              is specific but not necessarily the speaker's)

---

WORD: you
  type:       personal pronoun, second person, singular or plural, subject or object
  function:   addressee-reference operator — inserts the listener as subject
              or object depending on position. does not require backward
              resolution; the referent is always the addressee
  attaches:   forward to the next verb when in subject position; backward to
              the preceding verb or preposition when in object position.
              position is determined by word order relative to the verb
  signals:    second person, singular or plural (ambiguous without context),
              subject or object case (English "you" is case-neutral).
              referent is always unambiguous — the person being addressed
  result:     does not produce a claim on its own. places ADDRESSEE into the
              subject or object position. subject: ADDRESSEE DID [verb].
              object: [subject] ACTED_ON ADDRESSEE
  not:        "your" (possessive — marks ownership by the addressee, not the
              addressee as agent or patient. "you run" vs "your dog"),
              "I" (first person — the speaker, not the listener),
              "they" (third person plural — neither speaker nor listener.
              "you" always means the person being spoken to)
  notes:      "you" is ambiguous between singular and plural. some dialects
              resolve this with "y'all," "you guys," "youse." the system
              should default to singular unless a plural signal is present
              in context. also used for generic/impersonal reference
              ("you never know") — in that case it functions more like "one"
              and refers to people-in-general, not the specific addressee

---

WORD: your
  type:       possessive determiner, second person
  function:   ownership marker — binds the following noun to the addressee as
              possessor. occupies the determiner slot and also marks the noun
              as specific
  attaches:   forward to the next noun phrase. claims that noun as belonging
              to or associated with the addressee
  signals:    second person possessor, singular or plural (ambiguous).
              the noun is a specific known instance AND belongs to the addressee.
              implies definiteness
  result:     ADDRESSEE HAS [noun] or [noun] PART_OF ADDRESSEE's domain.
              also marks the noun as INSTANCE (specific), not TYPE
  not:        "you" (subject/object pronoun — "you" is the agent or patient,
              "your" marks ownership. "you run" vs "your dog"),
              "yours" (possessive pronoun, standalone — "your" must attach to
              a noun, "yours" replaces the noun. "your book" vs "the book
              is yours"),
              "my" (first person possessive — speaker's ownership, not
              addressee's ownership)

---

WORD: he
  type:       personal pronoun, third person, singular, masculine, subject
  function:   backward reference — substitutes for the last singular masculine
              (or contextually male) noun. resolves to that noun's identity
              for all following attachment purposes
  attaches:   backward to the last singular masculine/male noun in context
              (same sentence first, then prior sentence). once resolved,
              "he" becomes that noun for downstream processing. then attaches
              forward to the next verb as subject
  signals:    third person, singular, masculine, subject case, animate.
              the referent is already known from context
  result:     does not produce a claim on its own. substitutes the resolved
              masculine noun into the subject position. all claims fire
              against the resolved referent: [referent] DID [verb], etc.
  not:        "him" (same referent but object case — "him" receives action,
              "he" performs it),
              "his" (possessive — marks ownership by the masculine referent,
              not the referent as agent),
              "she" (feminine counterpart — resolves to female/feminine nouns),
              "it" (non-gendered/non-animate — "he" is specifically masculine
              and typically animate),
              "they" (plural, or singular gender-neutral — "he" commits to
              masculine singular)

---

WORD: him
  type:       personal pronoun, third person, singular, masculine, object
  function:   backward reference, object position — substitutes for the last
              singular masculine noun AND places it in the object slot of
              the preceding verb or preposition
  attaches:   backward in two ways: (1) resolves referent by finding the last
              singular masculine noun, (2) fills the object slot of the
              preceding verb or preposition
  signals:    third person, singular, masculine, object case, animate.
              the referent is acted upon, not acting
  result:     does not produce a claim on its own. places the resolved
              masculine referent into the object position:
              [subject] ACTED_ON [referent], [subject] DID [verb] → target: [referent]
  not:        "he" (same referent but subject case — "he" performs, "him" receives),
              "his" (possessive — marks ownership, not object role.
              "give him the book" vs "his book"),
              "her" as object pronoun (feminine counterpart — resolves to
              female/feminine nouns),
              "them" (plural object — "him" is singular masculine)

---

WORD: his
  type:       possessive determiner, third person, singular, masculine
  function:   ownership marker with backward reference — resolves to the last
              singular masculine noun, then binds the following noun to that
              referent as possessor. occupies the determiner slot
  attaches:   backward to the last singular masculine noun for referent
              resolution, AND forward to the next noun phrase for possession
              binding
  signals:    third person, singular, masculine possessor. the following noun
              is a specific instance belonging to the masculine referent.
              implies definiteness
  result:     [masculine referent] HAS [noun] or [noun] PART_OF [masculine
              referent]'s domain. also marks the noun as INSTANCE (specific)
  not:        "he" (subject pronoun — the referent as agent, not as possessor),
              "him" (object pronoun — the referent as patient, not as possessor),
              "her" as possessive (feminine counterpart — resolves to
              female/feminine nouns),
              "its" (non-gendered possessive — "his" is specifically masculine
              and typically animate)
  notes:      "his" can also function as a standalone possessive pronoun
              ("the book is his"), in which case it does not attach forward
              to a noun but instead substitutes for a noun phrase with
              possession already bound. primary behavior is the determiner form

---

WORD: she
  type:       personal pronoun, third person, singular, feminine, subject
  function:   backward reference — substitutes for the last singular feminine
              (or contextually female) noun. resolves to that noun's identity
              for all following attachment purposes
  attaches:   backward to the last singular feminine/female noun in context
              (same sentence first, then prior sentence). once resolved,
              "she" becomes that noun for downstream processing. then attaches
              forward to the next verb as subject
  signals:    third person, singular, feminine, subject case, animate.
              the referent is already known from context
  result:     does not produce a claim on its own. substitutes the resolved
              feminine noun into the subject position. all claims fire
              against the resolved referent: [referent] DID [verb], etc.
  not:        "her" as pronoun (same referent but object case — "her" receives
              action, "she" performs it),
              "her" as possessive (marks ownership by the feminine referent,
              not the referent as agent),
              "he" (masculine counterpart — resolves to male/masculine nouns),
              "it" (non-gendered/non-animate — "she" is specifically feminine
              and typically animate),
              "they" (plural, or singular gender-neutral — "she" commits to
              feminine singular)

---

WORD: her (pronoun)
  type:       personal pronoun, third person, singular, feminine, object
  function:   backward reference, object position — substitutes for the last
              singular feminine noun AND places it in the object slot of
              the preceding verb or preposition
  attaches:   backward in two ways: (1) resolves referent by finding the last
              singular feminine noun, (2) fills the object slot of the
              preceding verb or preposition
  signals:    third person, singular, feminine, object case, animate.
              the referent is acted upon, not acting
  result:     does not produce a claim on its own. places the resolved
              feminine referent into the object position:
              [subject] ACTED_ON [referent], [subject] DID [verb] → target: [referent]
  not:        "she" (same referent but subject case — "she" performs,
              "her" as pronoun receives),
              "her" as possessive (determines the following noun's ownership —
              same surface form but entirely different function. "I saw her"
              vs "her dog"),
              "him" (masculine counterpart — resolves to male/masculine nouns),
              "them" (plural object — "her" is singular feminine)
  notes:      disambiguation between "her" (pronoun) and "her" (possessive)
              is positional: if "her" is followed by a noun phrase, it is
              possessive. if "her" follows a verb or preposition with no
              noun afterward, it is the object pronoun

---

WORD: her (possessive)
  type:       possessive determiner, third person, singular, feminine
  function:   ownership marker with backward reference — resolves to the last
              singular feminine noun, then binds the following noun to that
              referent as possessor. occupies the determiner slot
  attaches:   backward to the last singular feminine noun for referent
              resolution, AND forward to the next noun phrase for possession
              binding
  signals:    third person, singular, feminine possessor. the following noun
              is a specific instance belonging to the feminine referent.
              implies definiteness
  result:     [feminine referent] HAS [noun] or [noun] PART_OF [feminine
              referent]'s domain. also marks the noun as INSTANCE (specific)
  not:        "she" (subject pronoun — the referent as agent, not as possessor),
              "her" as pronoun (object pronoun — the referent as patient, not
              as possessor. same surface form, different slot),
              "hers" (possessive pronoun, standalone — "her" as possessive
              must attach to a noun, "hers" replaces the noun entirely.
              "her book" vs "the book is hers"),
              "his" (masculine counterpart — resolves to male/masculine nouns)
  notes:      see "her (pronoun)" notes for positional disambiguation.
              if "her" precedes a noun, it is this possessive form.
              if "her" follows a verb or preposition without a following
              noun, it is the object pronoun form

---

WORD: it
  type:       personal pronoun, third person, singular, non-gendered
  function:   backward reference — substitutes for the last singular
              non-animate (or ungendered) noun. resolves to that noun's
              identity for all following attachment purposes
  attaches:   backward to the last singular noun in context (same sentence
              first, then prior sentence). once resolved, "it" becomes
              that noun for all downstream processing in the current clause
  signals:    singular, non-gendered (or gender-unknown), specific referent
              (the thing is already known from context)
  result:     does not produce a claim on its own. substitutes the referent
              noun into the subject/object position. all claims that would
              fire against "it" fire against the resolved noun instead
  not:        "this" (proximal demonstrative — points to something nearby or
              just mentioned, with emphasis. "it" is neutral reference,
              "this" is active selection),
              "that" (distal demonstrative or relative pronoun — can do
              reference like "it" but also introduces relative clauses.
              "it" never introduces a relative clause),
              "they" (plural or gender-neutral animate — "it" is singular
              and typically non-animate),
              "he/she" (gendered animate — "it" is non-gendered and
              typically non-animate)
  notes:      ambiguity arises when multiple singular nouns precede "it".
              default resolution is the LAST singular noun. if that produces
              a semantic contradiction, the system should flag the ambiguity
              rather than guess. also used as expletive subject with no
              referent ("it is raining," "it seems that...") — in that case,
              "it" fills a structural subject slot but resolves to nothing.
              the system should detect the absence of a viable referent and
              mark the subject slot as EMPTY/EXPLETIVE

---

WORD: its
  type:       possessive determiner, third person, singular, non-gendered
  function:   ownership marker with backward reference — resolves to the last
              singular non-animate (or ungendered) noun, then binds the
              following noun to that referent as possessor. occupies the
              determiner slot
  attaches:   backward to the last singular non-gendered noun for referent
              resolution, AND forward to the next noun phrase for possession
              binding
  signals:    third person, singular, non-gendered possessor. the following
              noun is a specific instance belonging to or associated with
              the non-gendered referent. implies definiteness
  result:     [non-gendered referent] HAS [noun] or [noun] PART_OF
              [non-gendered referent]. also marks the noun as INSTANCE (specific)
  not:        "it" (subject/object pronoun — "it" fills agent or patient slot,
              "its" marks ownership. "it broke" vs "its handle"),
              "it's" (contraction of "it is" or "it has" — completely different
              function despite near-identical surface form. "its" is NEVER a
              contraction),
              "his/her" as possessives (gendered counterparts — "its" is
              non-gendered and typically non-animate),
              "their" (plural possessive — "its" is singular)

---

WORD: we
  type:       personal pronoun, first person, plural, subject
  function:   group-reference operator — inserts the speaker plus at least
              one other entity as a collective subject. does not require
              backward resolution for the speaker component; may require
              context to identify who else is included
  attaches:   forward to the next verb. fills the subject slot with a
              collective entity that includes the speaker
  signals:    first person, plural, subject case. the speaker is one of the
              agents. always includes the speaker; the other members are
              determined by context
  result:     does not produce a claim on its own. places SPEAKER_GROUP
              (speaker + contextually identified others) into the subject
              position: SPEAKER_GROUP DID [verb], SPEAKER_GROUP CAN_DO [verb], etc.
  not:        "I" (first person singular — speaker alone, no others included),
              "us" (same referent group but object case — "us" receives action,
              "we" performs it),
              "they" (third person plural — excludes the speaker entirely.
              "we" always includes the speaker, "they" never does),
              "you" (second person — the addressee, not the speaker's group)
  notes:      "we" has an inclusive/exclusive ambiguity: inclusive "we" means
              speaker + listener ("we should go" = you and I), exclusive "we"
              means speaker + others but not the listener ("we went yesterday"
              = my group, not you). English does not grammatically distinguish
              these. the system should flag the ambiguity when both readings
              are plausible

---

WORD: us
  type:       personal pronoun, first person, plural, object
  function:   group-reference operator, object position — inserts the speaker
              plus at least one other entity as the collective target or
              recipient of a verb or preposition
  attaches:   backward to the preceding verb or preposition. fills the object
              slot with a collective entity that includes the speaker
  signals:    first person, plural, object case. the speaker's group is the
              patient or recipient, not the agent
  result:     does not produce a claim on its own. places SPEAKER_GROUP into
              the object position: [subject] ACTED_ON SPEAKER_GROUP,
              [subject] DID [verb] → target: SPEAKER_GROUP
  not:        "we" (same referent group but subject case — "we" performs,
              "us" receives),
              "our" (possessive — marks ownership by the speaker's group,
              not the group as patient),
              "me" (first person singular object — speaker alone, no group),
              "them" (third person plural object — excludes the speaker)

---

WORD: our
  type:       possessive determiner, first person, plural
  function:   ownership marker — binds the following noun to the speaker's
              group as possessor. occupies the determiner slot and marks
              the noun as specific
  attaches:   forward to the next noun phrase. claims that noun as belonging
              to or associated with the speaker's group
  signals:    first person, plural possessor. the following noun is a specific
              instance belonging to or shared by the speaker's group.
              implies definiteness
  result:     SPEAKER_GROUP HAS [noun] or [noun] PART_OF SPEAKER_GROUP's
              domain. also marks the noun as INSTANCE (specific)
  not:        "we" (subject pronoun — the group as agent, not as possessor),
              "us" (object pronoun — the group as patient, not as possessor),
              "ours" (possessive pronoun, standalone — "our" must attach to
              a noun, "ours" replaces the noun. "our house" vs "the house
              is ours"),
              "my" (first person singular possessive — speaker alone, not
              the group),
              "their" (third person plural possessive — excludes the speaker)

---

WORD: they
  type:       personal pronoun, third person, plural (or singular
              gender-neutral), subject
  function:   backward reference — substitutes for the last plural noun or
              noun group, OR for a singular noun whose gender is unknown or
              irrelevant. resolves to that noun's identity for all following
              attachment purposes
  attaches:   backward to the last plural noun or compound noun group in
              context (same sentence first, then prior sentence). once
              resolved, "they" becomes that noun/group for downstream
              processing. then attaches forward to the next verb as subject
  signals:    third person, plural (default) or singular gender-neutral,
              subject case. the referent is already known from context.
              when plural, always refers to multiple entities
  result:     does not produce a claim on its own. substitutes the resolved
              noun/group into the subject position. all claims fire against
              the resolved referent: [referent-group] DID [verb], etc.
              when plural, claims may distribute across members
  not:        "we" (first person plural — includes the speaker. "they"
              excludes the speaker),
              "he/she" (third person singular, gendered — "they" as singular
              is specifically gender-neutral),
              "it" (third person singular, non-animate — "they" is either
              plural or singular-animate-gender-neutral),
              "those" (demonstrative — can reference a group but adds
              distal pointing. "they" is neutral reference, "those" is
              active selection with distance)
  notes:      singular "they" for a known individual whose gender is
              unspecified or non-binary is increasingly standard. the system
              should prefer plural resolution when a plural antecedent is
              available, but fall back to singular gender-neutral when only
              a singular antecedent is present and gendered pronouns would
              be inappropriate or inaccurate

---

WORD: them
  type:       personal pronoun, third person, plural (or singular
              gender-neutral), object
  function:   backward reference, object position — substitutes for the last
              plural noun or noun group AND places it in the object slot of
              the preceding verb or preposition
  attaches:   backward in two ways: (1) resolves referent by finding the last
              plural noun or noun group, (2) fills the object slot of the
              preceding verb or preposition
  signals:    third person, plural (default) or singular gender-neutral,
              object case. the referent group is acted upon, not acting
  result:     does not produce a claim on its own. places the resolved
              plural referent into the object position:
              [subject] ACTED_ON [referent-group],
              [subject] DID [verb] → target: [referent-group]
  not:        "they" (same referent but subject case — "they" performs,
              "them" receives),
              "their" (possessive — marks ownership by the group, not the
              group as patient. "give them the tools" vs "their tools"),
              "us" (first person plural object — includes the speaker.
              "them" excludes the speaker),
              "him/her" (singular gendered object — "them" is plural or
              singular gender-neutral)

---

WORD: their
  type:       possessive determiner, third person, plural (or singular
              gender-neutral)
  function:   ownership marker with backward reference — resolves to the last
              plural noun or noun group (or singular gender-neutral noun),
              then binds the following noun to that referent as possessor.
              occupies the determiner slot
  attaches:   backward to the last plural noun or noun group for referent
              resolution, AND forward to the next noun phrase for possession
              binding
  signals:    third person, plural (default) or singular gender-neutral,
              possessor. the following noun is a specific instance belonging
              to or associated with the group. implies definiteness
  result:     [referent-group] HAS [noun] or [noun] PART_OF
              [referent-group]'s domain. also marks the noun as INSTANCE
              (specific)
  not:        "they" (subject pronoun — the group as agent, not as possessor),
              "them" (object pronoun — the group as patient, not as possessor),
              "theirs" (possessive pronoun, standalone — "their" must attach
              to a noun, "theirs" replaces the noun. "their house" vs
              "the house is theirs"),
              "our" (first person plural possessive — includes the speaker.
              "their" excludes the speaker),
              "its" (third person singular non-gendered possessive — "their"
              is plural or singular gender-neutral for animates, "its" is
              singular non-animate)

---

## Group 3: Modal Operators

WORD: can
  type:       modal operator, positive capacity
  function:   capacity marker — marks the following verb as an affordance the subject possesses. asserts that the ability exists, not that it is currently being exercised
  attaches:   forward to the following verb
  signals:    capacity, affordance, ability. the subject has the structural or physical means to perform the action. present tense, general capability
  result:     [subject] CAN_DO [verb] = True
  not:        "may" (permission or possibility, not capacity — "you may leave" grants authorization, "you can leave" asserts you have the ability to),
              "could" (conditional or past capacity — "can" is present and unconditional),
              "will" (future intention or prediction — "can" says nothing about whether the action will happen, only that it's possible),
              "does" (habitual actuality — "she does swim" means she habitually swims, "she can swim" means she has the capacity regardless of habit)
  notes:      in casual speech "can" often replaces "may" for permission ("can I go?"). the system should treat this as capacity unless explicit permission context is present

---

WORD: cannot
  type:       modal operator, negative capacity
  function:   rejection operator — marks the following verb connection as False. denies the capacity, not the current action
  attaches:   forward to the following verb
  signals:    negation of affordance. the subject lacks the capacity entirely. not situational, not temporary (unless context overrides)
  result:     [subject] CAN_DO [verb] = False
              equivalent: [subject] REJECTS [verb] = True
  not:        "do not / don't" (denies current habit or choice, not capacity — "dogs don't fly" means they habitually don't, "dogs cannot fly" means they lack the capacity),
              "will not / won't" (denies intention or future action, not capacity),
              "must not" (denies permission, not capacity — "you must not enter" means you're forbidden, not incapable),
              "never" (frequency = zero, but doesn't deny capacity — "I never swim" doesn't mean I can't)

---

WORD: could
  type:       modal operator, conditional/past capacity
  function:   conditional capacity marker — marks the following verb as a capacity that is either (a) past tense, (b) hypothetical/conditional, or (c) softened/polite. the capacity is not asserted as present fact but as displaced from the current moment
  attaches:   forward to the following verb
  signals:    capacity under condition. either past ability ("I could run fast as a child"), hypothetical ability ("I could help if you asked"), or politeness softener ("could you pass the salt?"). always one degree removed from present-actual
  result:     [subject] CAN_DO [verb] = True, CONDITIONAL or PAST.
              the claim fires but is tagged as non-current — it does not assert present active capacity the way "can" does
  not:        "can" (present, unconditional capacity — "could" always carries displacement: past, hypothetical, or polite),
              "would" (conditional willingness or habit, not capacity — "could" is about ability under conditions, "would" is about volition under conditions),
              "might" (possibility, not capacity — "I might go" says it's possible I'll go, "I could go" says I have the ability to go if conditions are met)
  notes:      disambiguation between past capacity and hypothetical capacity depends on tense context of surrounding clauses. "I could swim when I was young" = past. "I could swim if the pool were open" = hypothetical. the system should check for past-tense markers or conditional markers (if, were) in the clause

---

WORD: would
  type:       modal operator, conditional volition
  function:   conditional intention marker — marks the following verb as an action the subject is willing to perform or expects to perform, but only under some condition or in a hypothetical frame. the action is not actual
  attaches:   forward to the following verb
  signals:    volition under condition, hypothetical action, displaced intention. the subject has the willingness but the situation is not actual. also used for habitual past ("he would always sing")
  result:     [subject] DID [verb] = CONDITIONAL (hypothetical frame) or
              [subject] DID [verb] = HABITUAL_PAST (past habitual frame).
              the claim is generated but tagged as non-actual — it does not assert the action occurred or will occur in present reality
  not:        "will" (future intention, unconditional — "I will go" asserts commitment, "I would go" asserts willingness contingent on something),
              "could" (conditional capacity, not volition — "could" asks whether ability exists under conditions, "would" asks whether willingness exists under conditions),
              "should" (conditional obligation, not volition — "should" carries normative weight, "would" is volitional preference)
  notes:      habitual past usage ("when I was young I would walk to school every day") is functionally distinct from conditional usage. habitual past = repeated actual events now concluded. conditional = hypothetical non-actual events. surrounding tense and clause structure disambiguate

---

WORD: should
  type:       modal operator, normative obligation
  function:   obligation marker — marks the following verb as the expected, recommended, or normatively correct action. asserts that performing the verb is the right thing to do, but does not assert that it is happening or will happen
  attaches:   forward to the following verb
  signals:    obligation, recommendation, expectation. the action is normatively weighted — the subject is expected to do it. softer than "must" — failure to comply is a deviation, not a violation
  result:     [subject] REQUIRES [verb] = True, NORMATIVE.
              the claim fires as an expectation, not a fact. equivalent: there exists a norm or standard under which [subject] doing [verb] is correct
  not:        "must" (hard obligation or logical necessity — "must" is non-negotiable, "should" is a recommendation that can be overridden),
              "would" (conditional volition — "would" says what the subject wants to do under conditions, "should" says what the subject ought to do regardless of want),
              "could" (conditional capacity — "could" says the subject is able, "should" says the subject is expected to),
              "ought to" (near-synonym — functionally identical in most contexts, but "ought to" carries slightly more moral weight in formal usage. the system can treat them as equivalent)

---

WORD: must
  type:       modal operator, hard obligation / logical necessity
  function:   necessity marker — marks the following verb as required, non-optional. either the subject is obligated to perform the action (deontic) or the action is logically entailed by evidence (epistemic: "it must be raining")
  attaches:   forward to the following verb
  signals:    hard obligation or logical certainty. deontic: the subject has no acceptable alternative. epistemic: the available evidence forces this conclusion. strongest modal force in the system
  result:     [subject] REQUIRES [verb] = True, MANDATORY (deontic) or
              [subject] DID/IS [verb] = True, INFERRED (epistemic).
              in deontic mode, the verb is flagged as non-optional for the subject. in epistemic mode, the verb is flagged as a strong inference from context
  not:        "should" (soft obligation — "should" allows deviation, "must" does not),
              "will" (prediction or intention — "will" says it's going to happen, "must" says it's required to happen. overlapping in effect but different in source),
              "cannot" (capacity denial — "must not" denies permission, "cannot" denies ability. "you must not leave" = you are forbidden; "you cannot leave" = you are unable),
              "have to" (near-synonym for deontic must — functionally equivalent in most contexts, but "have to" implies external compulsion while "must" can be self-imposed or logical)
  notes:      epistemic vs deontic disambiguation depends on subject animacy and clause type. "The door must be locked" = epistemic inference (evidence suggests it). "You must lock the door" = deontic obligation (you are required to). the system should check whether the subject can receive obligations (animate agent) or only descriptions (inanimate entity)

---

WORD: might
  type:       modal operator, epistemic possibility
  function:   possibility marker — marks the following verb as possible but uncertain. does not assert capacity, willingness, or obligation — only that the event is within the space of outcomes
  attaches:   forward to the following verb
  signals:    possibility, uncertainty, non-commitment. the speaker considers the action plausible but does not assert it will happen, can happen, or should happen. weaker than "may" in some registers, functionally equivalent in most
  result:     [subject] CAN_DO [verb] = POSSIBLE (not True, not False — undetermined).
              the claim is generated but tagged with uncertainty. it does not resolve to a boolean — it marks the action as open
  not:        "may" (possibility + permission — "might" is almost never used for permission, "may" can be either possibility or permission),
              "could" (conditional capacity — "could" says the subject has the ability under conditions, "might" says the event is possible regardless of the subject's capacity),
              "will" (assertion of future — "will" commits to the outcome, "might" explicitly refuses to commit),
              "can" (present capacity — "can" asserts ability exists now, "might" asserts only that an outcome is possible)

---

WORD: may
  type:       modal operator, permission / epistemic possibility
  function:   permission or possibility marker — either (a) grants or asserts permission for the subject to perform the verb, or (b) marks the verb as possible but uncertain (same as "might"). dual function, context-dependent
  attaches:   forward to the following verb
  signals:    permission (deontic): the subject is authorized to act. possibility (epistemic): the event could occur. these are distinct functions that share a surface form
  result:     permission mode: [subject] CAN_DO [verb] = True, PERMITTED (authorization granted by speaker or authority).
              possibility mode: [subject] CAN_DO [verb] = POSSIBLE (undetermined, same as "might")
  not:        "can" (capacity, not permission — "you can leave" asserts ability, "you may leave" grants authorization. in strict usage they differ, though casual speech blurs them),
              "might" (possibility only — "might" is never used for permission in standard usage),
              "must" (obligation, not permission — "must" requires action, "may" allows it),
              "shall" (formal future or legal obligation — "shall" in legal contexts means "is required to", "may" in legal contexts means "is allowed to")
  notes:      permission vs possibility disambiguation: if the subject is "I" and the sentence is a question ("may I go?"), it is permission. if the subject is third-person or the sentence is declarative ("it may rain"), it is possibility. the system should check sentence mood and subject person

---

WORD: will
  type:       modal operator, future intention / prediction
  function:   future marker — marks the following verb as a committed future action (if subject is animate agent) or a predicted future state (if subject is inanimate or the clause is observational). asserts that the event is expected to occur
  attaches:   forward to the following verb
  signals:    futurity, commitment, prediction. the action has not happened yet but is asserted as going to happen. strongest future commitment short of "shall" in formal registers
  result:     [subject] DID [verb] = FUTURE (the claim is generated with future tense tag — it will fire when the time resolves).
  not:        "would" (conditional future — "will" is unconditional commitment, "would" requires a condition to be met),
              "shall" (formal/legal obligation or first-person future — in modern usage "shall" is more formal or carries legal obligation; "will" is the standard future marker),
              "can" (capacity — "will" says it's going to happen, "can" says it's possible. "he can run" ≠ "he will run"),
              "may/might" (possibility — "will" commits to the outcome, "may/might" leave it open)
  notes:      "will" also functions as a noun (volition, testament) but the system should treat those as separate lexical entries. as a modal operator, "will" is exclusively a future/intention marker

---

WORD: shall
  type:       modal operator, formal future / legal obligation
  function:   formal future or obligation marker — in everyday usage, marks the following verb as future action (first person) with slightly formal register. in legal/regulatory contexts, marks the verb as a binding obligation equivalent to "must"
  attaches:   forward to the following verb
  signals:    formal future (first person: "I shall return") or binding obligation (legal/regulatory: "the contractor shall deliver"). carries more authority and formality than "will"
  result:     everyday: [subject] DID [verb] = FUTURE (same as "will" but with formal register tag).
              legal: [subject] REQUIRES [verb] = True, MANDATORY (same as "must" — non-optional binding obligation)
  not:        "will" (standard future — "shall" is formal or carries legal force, "will" is neutral future. in modern casual English they are nearly interchangeable for first person, but "shall" is marked/formal),
              "must" (hard obligation — in non-legal contexts "must" is obligation and "shall" is future. in legal contexts they converge, but "shall" is the standard legal term),
              "should" (soft obligation — "should" recommends, "shall" in legal contexts requires),
              "may" (permission — in legal drafting, "may" = is permitted, "shall" = is required. opposite poles of the same axis)
  notes:      "shall" is increasingly rare in casual modern English and may be interpreted as archaic or overly formal. in legal, regulatory, and contractual text it remains the standard obligation marker and should be treated as equivalent to "must" in those contexts

---

## Group 4: Copulas & Auxiliaries

WORD: is
  type:       copula, present tense, third person singular
  function:   identity/property linker — connects a singular subject to a predicate,
              asserting that the subject either IS_A (category membership) or
              HAS_PROPERTY (trait assignment) the predicate. serves as the primary
              claim-producing bridge between subject and complement
  attaches:   backward to the preceding singular subject noun, forward to the
              following predicate (noun, adjective, or prepositional phrase)
  signals:    present tense, singular subject (third person), active state —
              the link holds NOW, not in the past or hypothetically
  result:     if predicate is a noun: [subject] IS_A [predicate noun] = True
              ("the dog is a mammal" → dog IS_A mammal)
              if predicate is an adjective: [subject] HAS_PROPERTY [predicate adj] = True
              ("the dog is big" → dog HAS_PROPERTY big)
              if predicate is a location: [subject] LOCATED [predicate] = True
              ("the dog is outside" → dog LOCATED outside)
  not:        "are" (same function but plural or second-person subject —
              "is" requires singular third-person),
              "was" (same function but past tense — "is" asserts the link holds now,
              "was" asserts it held before and may no longer),
              "has" (possession or auxiliary — "is" links identity/property,
              "has" links ownership or marks perfect aspect. "the dog is a bone"
              is nonsense; "the dog has a bone" is possession),
              "does" (auxiliary for emphasis or questions — "is" produces claims
              directly, "does" modifies verb processing)
  notes:      "is" also serves as an auxiliary in progressive constructions
              ("the dog is running"). in that case it does not produce IS_A or
              HAS_PROPERTY — it combines with the present participle to signal
              ongoing action: [subject] DID [verb] with aspect = ONGOING.
              the system should detect this when the complement is a verb+ing form
              rather than a noun or adjective

---

WORD: are
  type:       copula, present tense, plural / second person singular
  function:   identity/property linker, plural — connects a plural subject (or
              "you") to a predicate, asserting category membership or trait
              assignment across all members of the subject set. mechanically
              identical to "is" except it requires a plural or second-person subject
  attaches:   backward to the preceding plural subject noun (or "you"), forward
              to the following predicate (noun, adjective, or prepositional phrase)
  signals:    present tense, plural subject (or second person singular/plural),
              active state — the link holds NOW and applies to all members of the set
  result:     if predicate is a noun: [subject_set] IS_A [predicate noun] = True
              (distributes: each member IS_A)
              if predicate is an adjective: [subject_set] HAS_PROPERTY [predicate adj] = True
              (distributes: each member HAS_PROPERTY)
              if predicate is a location: [subject_set] LOCATED [predicate] = True
              "dogs are mammals" → dog(type) IS_A mammal
              "dogs are loud" → dog(type) HAS_PROPERTY loud
  not:        "is" (singular third-person — "are" requires plural or second-person),
              "were" (past tense plural — "are" asserts the link holds now,
              "were" asserts it held before),
              "am" (first person singular — "I am" vs "we are" vs "they are"),
              "have" (possession or auxiliary — "are" links properties,
              "have" links ownership)
  notes:      like "is", also serves as progressive auxiliary ("they are running").
              when followed by a present participle, does not produce IS_A/HAS_PROPERTY
              but signals ongoing action. also appears in passive constructions
              ("they are seen") — when followed by a past participle, signals
              passive voice: [object] ACTED_ON by [implied agent]

---

WORD: was
  type:       copula, past tense, singular (first/third person)
  function:   past-state identity/property linker — connects a singular subject
              to a predicate and asserts that the link HELD in the past. the
              connection may or may not still hold in the present; the claim is
              anchored to a prior time
  attaches:   backward to the preceding singular subject noun (first or third person),
              forward to the following predicate (noun, adjective, prepositional phrase)
  signals:    past tense, singular subject, completed or prior state — the link
              existed at some previous time. carries an implicit "but maybe not now"
              unless context indicates persistence
  result:     if predicate is a noun: [subject] IS_A [predicate noun] = True, tense = PAST
              ("she was a teacher" → she IS_A teacher, tense = PAST)
              if predicate is an adjective: [subject] HAS_PROPERTY [predicate adj] = True, tense = PAST
              ("the soup was hot" → soup HAS_PROPERTY hot, tense = PAST)
              if predicate is a location: [subject] LOCATED [predicate] = True, tense = PAST
  not:        "is" (present tense — "is" asserts NOW, "was" asserts THEN.
              "the door is open" = currently open; "the door was open" = it was
              open at some point, status now uncertain),
              "were" (past tense but plural, or subjunctive — "was" is singular
              indicative, "were" is plural indicative or singular subjunctive),
              "had been" (past perfect — "was" locates in simple past, "had been"
              locates in a past-before-the-past),
              "used to be" (habitual past — explicitly signals the state no longer
              holds. "was" leaves current status ambiguous)
  notes:      "was" also serves as a past progressive auxiliary ("she was running")
              and a past passive auxiliary ("she was seen"). progressive: when
              followed by verb+ing, signals past ongoing action. passive: when
              followed by past participle, signals [subject] ACTED_ON by [agent],
              tense = PAST

---

WORD: were
  type:       copula, past tense, plural / second person / subjunctive singular
  function:   past-state identity/property linker, plural — connects a plural
              subject (or "you", or subjunctive singular) to a predicate and
              asserts that the link HELD in the past. also serves as the
              subjunctive form for hypothetical/counterfactual statements
  attaches:   backward to the preceding plural subject (or "you", or subjunctive
              singular subject), forward to the following predicate
  signals:    past tense, plural (or second person, or subjunctive), completed
              or prior state. in subjunctive use, signals COUNTERFACTUAL —
              the state is hypothetical, not actual
  result:     indicative: [subject_set] IS_A/HAS_PROPERTY [predicate] = True, tense = PAST
              (distributes across set members)
              subjunctive: [subject] IS_A/HAS_PROPERTY [predicate] = HYPOTHETICAL
              "the dogs were loud" → dog_set HAS_PROPERTY loud, tense = PAST
              "if I were rich" → I HAS_PROPERTY rich, mode = COUNTERFACTUAL
  not:        "was" (singular past indicative — "were" is plural past indicative
              OR singular subjunctive. "she was tired" = actual past state;
              "if she were tired" = hypothetical state),
              "are" (present tense plural — "are" asserts NOW, "were" asserts THEN),
              "had been" (past perfect — further back in time than simple "were"),
              "would be" (conditional — signals dependent outcome rather than
              counterfactual state framing)
  notes:      the subjunctive use ("if I were", "I wish I were") is critical to
              distinguish from indicative. the system should detect subjunctive
              context when "were" follows "if", "wish", "suppose", "as though",
              or other hypothetical triggers, and tag the result as COUNTERFACTUAL
              rather than PAST

---

WORD: has
  type:       auxiliary verb (perfect aspect) / possession verb, present tense,
              third person singular
  function:   dual function depending on complement:
              (1) POSSESSION: links subject to an owned object — asserts the subject
              holds, contains, or is associated with the object.
              (2) PERFECT AUXILIARY: when followed by a past participle, marks the
              action as completed with present relevance — the action happened
              before now and its result persists
  attaches:   backward to the preceding singular subject (third person),
              forward to the following noun (possession) or past participle (perfect)
  signals:    present tense, singular third-person subject.
              possession: ownership/association link active NOW.
              perfect: completed action with current relevance — the past event
              matters to the present moment
  result:     possession: [subject] HAS_FEATURE [object] = True
              ("the dog has a collar" → dog HAS_FEATURE collar)
              perfect: [subject] DID [verb] = True, aspect = PERFECT, tense = PRESENT
              ("the dog has eaten" → dog DID eat, aspect = PERFECT —
              the eating is done and the dog is currently in a post-eating state)
  not:        "have" (same dual function but plural or first/second person —
              "has" requires singular third-person),
              "had" (past tense of both functions — "has" = present possession
              or present-perfect; "had" = past possession or past-perfect),
              "is" (identity/property link — "has" links ownership, "is" links
              identity. "the dog has big" is ungrammatical; "the dog is big" is
              property assignment; "the dog has bigness" would be possession),
              "owns" (explicit ownership verb — "has" is broader than ownership;
              it covers features, parts, and associations. "the house has a roof"
              is PART_OF, not ownership)
  notes:      distinguishing possession from perfect auxiliary is critical. the
              system should check: if the word following "has" is a past participle
              (eaten, gone, been, seen), treat as perfect auxiliary. if the following
              word is a noun or noun phrase, treat as possession. edge case:
              "has got" — colloquial possession ("she has got a car" = she has a car)

---

WORD: have
  type:       auxiliary verb (perfect aspect) / possession verb, present tense,
              first/second person and plural
  function:   dual function identical to "has" but for plural or first/second
              person subjects:
              (1) POSSESSION: links subject to an owned/associated object.
              (2) PERFECT AUXILIARY: when followed by a past participle, marks
              action as completed with present relevance
  attaches:   backward to the preceding subject (first person, second person,
              or third person plural), forward to the following noun (possession)
              or past participle (perfect)
  signals:    present tense, non-third-person-singular subject.
              possession: ownership/association active NOW.
              perfect: completed action with present relevance
  result:     possession: [subject] HAS_FEATURE [object] = True
              ("we have a plan" → we HAS_FEATURE plan)
              perfect: [subject] DID [verb] = True, aspect = PERFECT, tense = PRESENT
              ("they have arrived" → they DID arrive, aspect = PERFECT)
  not:        "has" (same function, third person singular — "have" is everything else),
              "had" (past tense — "have eaten" = completed with present relevance;
              "had eaten" = completed before some past reference point),
              "have to" (obligation — entirely different function from possession
              or perfect. "I have to go" = I REQUIRES go, expressing necessity.
              the system should detect "have to" / "have got to" as an obligation
              operator, not possession),
              "own" (explicit ownership — "have" is broader, covering features,
              parts, associations)
  notes:      "have to" / "have got to" as an obligation operator is a critical
              edge case. when "have" is followed by "to" + infinitive, it functions
              as a modal-like obligation marker: [subject] REQUIRES [verb] = True.
              this overrides both possession and perfect readings entirely

---

WORD: had
  type:       auxiliary verb (past perfect aspect) / possession verb, past tense,
              all persons
  function:   dual function, past-shifted:
              (1) PAST POSSESSION: links subject to an object that was owned/associated
              at a prior time — the link may no longer hold.
              (2) PAST PERFECT AUXILIARY: when followed by a past participle, marks
              an action as completed BEFORE another past event — establishes
              a past-before-the-past temporal layer
  attaches:   backward to the preceding subject (any person/number),
              forward to the following noun (past possession) or past participle
              (past perfect)
  signals:    past tense, all persons. past possession: ownership/association
              that held previously. past perfect: action completed before a past
              reference point — two layers of pastness
  result:     past possession: [subject] HAS_FEATURE [object] = True, tense = PAST
              ("she had a cat" → she HAS_FEATURE cat, tense = PAST)
              past perfect: [subject] DID [verb] = True, aspect = PERFECT, tense = PAST_PERFECT
              ("she had left before I arrived" → she DID leave, completed before
              the reference point of "I arrived")
  not:        "has/have" (present tense — "had" shifts both functions into the past.
              "has eaten" = done, relevant now; "had eaten" = done before some
              past event, relevant then),
              "was" (past copula — links identity/property in the past. "had"
              links possession in the past. "she was a teacher" vs "she had a degree"),
              "would have" (conditional perfect — hypothetical past completion.
              "had" is actual past; "would have" is counterfactual past),
              "did" (simple past auxiliary — "did" marks a past action simply;
              "had" + participle marks a past action relative to another past moment)
  notes:      "had" in conditional constructions ("had I known", "if she had gone")
              marks counterfactual past — the system should tag as COUNTERFACTUAL
              when "had" appears inverted before the subject or after "if" in a
              conditional clause

---

WORD: does
  type:       auxiliary verb, present tense, third person singular
  function:   verb-support operator — does not produce a claim on its own. serves
              three mechanical functions:
              (1) EMPHASIS: reinforces the truth of the following verb ("she DOES run").
              (2) QUESTION FORMATION: inverts with subject to form yes/no questions
              ("does she run?").
              (3) NEGATION SUPPORT: hosts "not" to negate the following verb
              ("she does not run")
  attaches:   forward to the following base-form verb. backward to the preceding
              singular third-person subject
  signals:    present tense, singular third-person subject. in emphatic use,
              signals assertion reinforcement (the speaker is insisting). in
              question use, signals interrogative mode. carries no semantic
              content of its own — purely structural
  result:     does not produce a claim independently. modifies how the following
              verb's claim fires:
              emphatic: [subject] DID [verb] = True, emphasis = REINFORCED, tense = PRESENT
              ("she does run every day" → she DID run, reinforced assertion)
              question: [subject] DID [verb] = ? (query, not assertion)
              negation host: when paired with "not", [subject] DID [verb] = False, tense = PRESENT
  not:        "is" (copula — links identity/property. "does" supports action verbs.
              "does she a teacher?" is ungrammatical; "is she a teacher?" is copular),
              "did" (past tense auxiliary — "does" is present, "did" is past),
              "do" (same function but plural/first/second person —
              "does" requires singular third-person),
              "makes/causes" (the lexical verb "do" meaning to perform/cause —
              the auxiliary "does" has no performative meaning, only structural support)

---

WORD: did
  type:       auxiliary verb, past tense, all persons
  function:   past-tense verb-support operator — does not produce a claim on its
              own. serves three mechanical functions shifted to past tense:
              (1) EMPHASIS: reinforces truth of a past action ("she DID run").
              (2) QUESTION FORMATION: inverts with subject for past questions
              ("did she run?").
              (3) NEGATION SUPPORT: hosts "not" for past negation
              ("she did not run")
  attaches:   forward to the following base-form verb. backward to the preceding
              subject (any person/number)
  signals:    past tense, all persons. past-shifts the following verb without
              requiring the verb to take past-tense morphology (the verb stays
              in base form: "did run", not "did ran"). in emphatic use, signals
              insistent past assertion
  result:     does not produce a claim independently. modifies the following verb:
              emphatic: [subject] DID [verb] = True, emphasis = REINFORCED, tense = PAST
              question: [subject] DID [verb] = ? tense = PAST
              negation host: when paired with "not", [subject] DID [verb] = False, tense = PAST
  not:        "does/do" (present tense auxiliaries — "did" is the past counterpart),
              "had" (past perfect auxiliary — "did" marks simple past, "had" + participle
              marks past-before-past. "she did eat" = she ate at that time;
              "she had eaten" = she ate before that time),
              "was/were" (past copula — "did" supports action verbs in the past,
              "was/were" links identity/property in the past),
              "done" (past participle — "did" is the finite auxiliary,
              "done" is the participial form used after "have/has/had")

---

WORD: do
  type:       auxiliary verb, present tense, first/second person and plural
  function:   verb-support operator — identical mechanical function to "does"
              but for non-third-person-singular subjects. serves emphasis,
              question formation, and negation support
  attaches:   forward to the following base-form verb. backward to the preceding
              subject (first person, second person, or third person plural)
  signals:    present tense, non-third-person-singular. same structural-only
              signaling as "does" — no semantic content, purely mechanical support
  result:     does not produce a claim independently. modifies the following verb:
              emphatic: [subject] DID [verb] = True, emphasis = REINFORCED, tense = PRESENT
              question: [subject] DID [verb] = ? tense = PRESENT
              negation host: [subject] DID [verb] = False, tense = PRESENT
              ("do they run?" → they DID run = ?)
              ("I do not run" → I DID run = False, tense = PRESENT)
  not:        "does" (same function, third person singular — "do" covers everything else),
              "did" (past tense — "do" is present, "did" is past),
              "do" as lexical verb (meaning to perform: "I do my homework" —
              here "do" IS the main verb meaning PERFORM/EXECUTE, producing
              [subject] DID [object]. the auxiliary "do" has no performative meaning)
  notes:      distinguishing auxiliary "do" from lexical "do" is a critical parse
              decision. auxiliary "do" is always followed by a base-form VERB
              ("do run", "do not eat"). lexical "do" is followed by a NOUN or
              noun phrase ("do homework", "do the dishes"). the system should
              check the word class of the complement to disambiguate

---

WORD: been
  type:       past participle of "be", used in perfect and passive constructions
  function:   participial state linker — never appears alone. requires a preceding
              auxiliary ("has/have/had") to function. completes perfect constructions
              of "be", signaling that a state or identity held over a duration
              leading up to a reference point, OR that an ongoing/passive process
              has been in effect
  attaches:   backward to preceding auxiliary ("has", "have", "had").
              forward to following predicate (adjective, noun, present participle,
              or past participle)
  signals:    perfect aspect applied to a state or identity. "has been" = the
              state has held from past to present. "had been" = the state held
              up to some past reference point. duration and continuity are implied
  result:     depends on what follows "been":
              adjective: [subject] HAS_PROPERTY [adj] = True, aspect = PERFECT
              ("she has been quiet" → she HAS_PROPERTY quiet, from past to now)
              noun: [subject] IS_A [noun] = True, aspect = PERFECT
              ("he has been a teacher" → he IS_A teacher, from past to now)
              present participle: [subject] DID [verb], aspect = PERFECT_PROGRESSIVE
              ("they have been running" → ongoing action from past through present)
              past participle (passive): [subject] ACTED_ON by [agent], aspect = PERFECT
              ("it has been repaired" → it ACTED_ON repair, completed with present relevance)
  not:        "was/were" (simple past copula — "was" marks a state at a past point;
              "has been" marks a state persisting FROM the past to now. "she was quiet"
              = quiet at that time; "she has been quiet" = quiet for a stretch
              leading to now),
              "being" (progressive participle — "been" is perfective, "being" is
              progressive. "has been seen" = completed; "is being seen" = in progress),
              "gone" (past participle of "go" — "has been" = state persistence;
              "has gone" = departure. "she has been to Paris" = she visited and returned;
              "she has gone to Paris" = she left for Paris and is there now)

---

WORD: being
  type:       present participle of "be", used in progressive and passive constructions
  function:   progressive state marker — signals that a state, identity assignment,
              or passive process is currently IN PROGRESS, not completed. requires
              a preceding form of "be" ("is", "was", "are", "were") to function
  attaches:   backward to preceding auxiliary form of "be" ("is", "are", "was", "were").
              forward to following predicate (adjective, noun, or past participle)
  signals:    progressive aspect applied to a state or process — the state is
              actively unfolding or the passive action is happening right now
              (or was happening at the reference time). implies temporariness
              and active change
  result:     depends on what follows "being":
              adjective: [subject] HAS_PROPERTY [adj] = True, aspect = PROGRESSIVE
              ("she is being quiet" → she HAS_PROPERTY quiet, actively/temporarily
              right now — implies this is deliberate or unusual behavior)
              noun: [subject] IS_A [noun] = True, aspect = PROGRESSIVE
              ("he is being a fool" → he IS_A fool, temporarily/performatively)
              past participle (passive progressive): [subject] ACTED_ON by [agent],
              aspect = PROGRESSIVE
              ("the house is being built" → house ACTED_ON build, in progress now)
  not:        "been" (perfective participle — "been" marks a state as completed
              or persisting through a duration. "being" marks a state as in progress.
              "has been repaired" = repair is done; "is being repaired" = repair
              is happening now),
              "is/are" (simple copula — "is quiet" states a property flatly;
              "is being quiet" adds progressive aspect, implying the quietness
              is temporary, deliberate, or noteworthy. "the dog is good" = general
              trait; "the dog is being good" = behaving well right now),
              "becoming" (inchoative — signals transition into a state. "being"
              signals currently occupying a state. "is becoming loud" = getting louder;
              "is being loud" = currently loud)
  notes:      "being" before an adjective strongly implies the behavior is CHOSEN
              or TEMPORARY rather than inherent. "she is kind" = permanent trait;
              "she is being kind" = acting kind right now, possibly unusually so.
              the system should tag progressive-state claims with temporality = TEMPORARY
              and volitionality = DELIBERATE when the subject is animate

---

## Group 5: Negation, Quantifiers & Relative/Interrogative

WORD: not
  type:       negation operator
  function:   boolean inverter — flips the truth value of the verb or
              predicate it attaches to. the claim still fires, but its
              result becomes False
  attaches:   forward to the following verb or predicate. in practice,
              attaches to the auxiliary or copula ("is not," "does not,"
              "can not") and through it to the main verb
  signals:    negation. the action, state, or property described by the
              verb is denied. does not specify why — capacity, choice,
              frequency, and permission are all compatible
  result:     inverts the boolean of the attached verb's claim.
              [subject] DID [verb] = False.
              [subject] HAS_PROPERTY [adjective] = False.
              does not produce a claim on its own — it modifies the
              truth value of the claim the verb would have produced
  not:        "never" (frequency = zero across all time — "not" denies a
              single instance or current state, "never" denies across
              the entire timeline),
              "no" (determiner negation — "no" attaches to a noun to deny
              existence of instances, "not" attaches to a verb to deny
              the action. "no dogs ran" vs "dogs did not run"),
              "cannot" (capacity denial — "not" is general-purpose negation,
              "cannot" specifically denies ability),
              "none" (pronoun — "none" substitutes for an absent quantity,
              "not" modifies a verb)
  notes:      "not" sometimes attaches to non-verb elements in idiomatic
              usage ("not every," "not all," "not only"). in these cases
              it inverts the scope of the following quantifier or
              adverb rather than a verb. the system should detect when
              "not" precedes a quantifier and apply negation to the
              quantifier's scope rather than searching for a verb

---

WORD: never
  type:       temporal negation operator
  function:   universal time negation — asserts that the verb's action has
              zero occurrences across all relevant time. combines negation
              with temporal scope: not just "didn't happen" but
              "didn't happen at any point"
  attaches:   forward to the following verb (or backward to the preceding
              verb if postposed). modifies the verb's claim to be false
              across all time points
  signals:    negation + universal temporal scope. frequency = zero.
              the action has not occurred, does not occur, and (by
              implication) will not occur. stronger than simple "not"
  result:     [subject] DID [verb] = False, across all time.
              does not deny capacity — only denies occurrence
  not:        "not" (single-instance negation — "I did not swim" denies
              one event, "I never swim" denies all events across time),
              "cannot" (capacity denial — "never" says it hasn't happened,
              "cannot" says it couldn't happen. "I never fly" vs
              "I cannot fly" — the first is frequency, the second is
              ability),
              "no" (determiner negation — "no" attaches to nouns,
              "never" attaches to verbs),
              "rarely" (low frequency but nonzero — "never" is absolute
              zero, "rarely" is near-zero)
  notes:      "never" can carry emotional emphasis beyond its literal
              meaning ("I would never do that" = strong denial, possibly
              of a single event rather than a true universal). the system
              should treat "never" as universal-temporal by default but
              flag when context suggests emphatic single-event denial

---

WORD: no
  type:       negative determiner
  function:   existence denial — attaches to a noun and asserts that zero
              instances of that noun exist in the relevant context.
              occupies the determiner slot (same slot as "the," "a,"
              "some") but fills it with negation
  attaches:   forward to the next noun phrase. denies the existence of
              any instance of that noun in the scope of the clause
  signals:    negation at the noun level. quantity = zero. no instances
              of the described thing exist, are present, or apply.
              functions as a determiner, not a verb modifier
  result:     COUNT([noun]) = 0 in context.
              the verb's claim may still structurally fire, but with
              an empty set as subject or object: "no dogs ran" →
              the set of dogs that ran is empty
  not:        "not" (verb negation — "not" denies the action, "no" denies
              the existence of the noun. "dogs did not run" vs
              "no dogs ran" — similar meaning but different attachment
              targets),
              "none" (standalone pronoun — "no" must attach to a noun,
              "none" replaces the noun entirely. "no answer" vs
              "none was given"),
              "zero" (numeric literal — "zero" is a specific count,
              "no" is a negation operator that happens to produce
              count = 0. "zero dogs" is arithmetic, "no dogs" is denial),
              "any" (in negative contexts "any" approaches "no" but is
              not inherently negative — "any" requires a negation
              operator elsewhere, "no" carries its own negation)
  notes:      "no" also functions as a standalone interjection or
              response particle ("No, I disagree"). in that usage it
              is not a determiner but a sentence-level rejection
              operator that negates the preceding proposition entirely.
              the system should distinguish based on whether "no" is
              followed by a noun (determiner) or stands alone /
              precedes a comma (interjection)

---

WORD: none
  type:       negative pronoun
  function:   zero-quantity substitution — stands in for a noun phrase and
              asserts that zero instances exist. replaces both the
              determiner and the noun with a single token meaning
              "not any of them"
  attaches:   backward to an established noun category from context
              (explicit or implied). "none" substitutes for that noun
              with count = 0. fills the subject or object slot in the
              clause
  signals:    quantity = zero, specific referent category (determined by
              context), pronominal (replaces a full noun phrase).
              the category of thing is known, but zero instances qualify
  result:     COUNT([contextual noun]) = 0.
              if subject: the verb's claim fires against an empty set.
              if object: the verb acted on nothing.
              "none arrived" → COUNT(arrivals from expected set) = 0
  not:        "no" (determiner — "no" attaches to a noun, "none" replaces
              the noun. "no students passed" vs "none passed"),
              "nothing" (negative pronoun for things/concepts — "none"
              refers to zero members of a known set, "nothing" refers
              to the absence of any thing at all. "none of the answers"
              vs "nothing happened"),
              "not any" (compositional equivalent — "none" is the fused
              single-token form. functionally similar but "none" is
              more definitive and occupies a pronoun slot),
              "zero" (numeric literal — "zero" is a count, "none" is a
              pronominal negation that implies "of the relevant set")

---

WORD: all
  type:       universal quantifier
  function:   scope expander — sets the following noun to TYPE-level,
              universal scope. the verb's claim applies to the entire
              category without exception. "all" does not alter the claim
              itself — it tells the system to apply the verb's claim
              across every member of the type
  attaches:   forward to the next noun phrase. modifies that noun's scope
              from default (ambiguous) to UNIVERSAL. can also attach
              backward to a pronoun ("they all," "we all") to reinforce
              universal scope on an already-resolved referent
  signals:    universal scope, completeness, no exceptions. the noun
              operates at TYPE level — the claim is about the category,
              not an instance. collective framing — the set is treated
              as a whole
  result:     sets noun scope to TYPE / UNIVERSAL. does not produce or
              modify any claim. the verb's claim fires unchanged —
              "all dogs bark" → dog CAN_DO bark = True, applied at
              TYPE level with universal scope. the quantifier is
              consumed once scope is set
  not:        "every" (also universal, but distributive — "all dogs"
              frames the group collectively, "every dog" iterates
              individually. "all students lifted the table" permits
              a collective reading, "every student lifted the table"
              forces individual readings),
              "some" (existential — scopes the noun to a subset, not
              the full type),
              "most" (majority but not universal — explicitly allows
              exceptions, "all" does not),
              "the" (specific instance — "the dogs" refers to a known
              group of instances, "all dogs" sets scope to the
              entire type),
              "any" (free-choice — "any dog" means whichever one you
              pick, "all dogs" means the complete category)
  notes:      "all" can also function as a degree adverb ("all wet,"
              "all gone") meaning "completely." in that usage it
              attaches to an adjective or participle and signals
              completeness of a property rather than universal scope
              over a set. the system should detect whether the
              following token is a noun (quantifier) or an
              adjective/participle (degree adverb)

---

WORD: some
  type:       existential quantifier
  function:   scope limiter — sets the following noun to TYPE-level,
              existential scope. the verb's claim applies to an
              unspecified subset of the category. at least one member
              qualifies, but the claim is not universal. "some" does
              not alter the claim — it tells the system to apply the
              verb's claim to a partial, indefinite subset of the type
  attaches:   forward to the next noun phrase. modifies that noun's scope
              from default (ambiguous) to EXISTENTIAL / SUBSET. also
              marks the noun as indefinite — the specific members are
              not identified
  signals:    existential scope, partial quantity, indefinite. at least
              one member qualifies but not necessarily all. the noun
              operates at TYPE level but scoped to a subset. introduces
              new information (unlike "the," which marks known referents)
  result:     sets noun scope to TYPE / EXISTENTIAL. does not produce or
              modify any claim. the verb's claim fires unchanged —
              "some dogs bark" → dog CAN_DO bark = True, applied at
              TYPE level with existential scope (true for a subset,
              not asserted for all). the quantifier is consumed once
              scope is set
  not:        "all" (universal — scopes to the entire type, no exceptions.
              "some" explicitly allows that other members may not qualify),
              "any" (free-choice or polarity-sensitive — "any" is
              indifferent to which member, "some" asserts that a
              qualifying subset exists. "some dogs bark" commits to
              existence, "any dog can bark" is indifferent to selection),
              "a/an" (indefinite article — introduces a single nonspecific
              instance, "some" introduces a nonspecific subset that
              may be one or many),
              "few" (small quantity with negative implication — "some" is
              neutral about whether the quantity is satisfying, "few"
              signals it is not),
              "several" (more specific count range — "several" implies
              more than two but not many, "some" is vague about quantity)

---

WORD: every
  type:       distributive universal quantifier
  function:   scope expander with distributive framing — sets the following
              noun to TYPE-level, universal scope, but with a distributive
              instruction: the verb's claim is applied to each member
              individually, not to the group as a collective. the claim
              itself is unchanged — only scope and distribution mode are set
  attaches:   forward to the next noun phrase (always singular noun form
              despite universal meaning). modifies that noun's scope to
              UNIVERSAL / DISTRIBUTIVE
  signals:    universal scope, distributive (individual-by-individual),
              singular noun form. no exceptions — the claim applies to
              every member, but each is treated separately
  result:     sets noun scope to TYPE / UNIVERSAL / DISTRIBUTIVE. does not
              produce or modify any claim. the verb's claim fires unchanged —
              "every dog barks" → dog CAN_DO bark = True, applied at TYPE
              level with universal scope, evaluated per individual. the
              difference from "all" is framing: "every" distributes,
              "all" collects
  not:        "all" (also universal but collective — "all dogs" treats
              the set as a whole, "every dog" treats each separately.
              "all students lifted the table" = they did it together
              is a valid reading, "every student lifted the table" =
              each did it alone),
              "each" (also distributive, but emphasizes separateness
              even more strongly. "every" is comfortable with large
              open sets, "each" implies a bounded, enumerable set.
              "every star in the sky" is natural, "each star in the
              sky" implies you could list them),
              "any" (free-choice — "any" selects one arbitrarily,
              "every" iterates through all),
              "some" (existential — a subset, not the full type)

---

WORD: each
  type:       distributive quantifier, strongly individuating
  function:   scope expander with strong distributive framing — sets the
              following noun to TYPE-level, universal scope, with the
              strongest possible distributive instruction: every member
              is treated as its own isolated case. no collective reading
              is possible. the claim itself is unchanged — only scope
              and distribution mode are set
  attaches:   forward to the next noun phrase (always singular noun form).
              can also attach backward as a floating quantifier
              ("the students each received a book"). modifies the
              noun's scope to UNIVERSAL / DISTRIBUTIVE / INDIVIDUAL
  signals:    universal scope, strongly distributive, individual-by-individual.
              emphasizes separateness — each member is its own case.
              typically implies a smaller, bounded, enumerable set
  result:     sets noun scope to TYPE / UNIVERSAL / DISTRIBUTIVE (strong).
              does not produce or modify any claim. the verb's claim
              fires unchanged — "each student passed" → student DID
              pass = True, applied at TYPE level with universal scope,
              evaluated per individual with no collective reading possible
  not:        "every" (also distributive universal, but looser — "every"
              allows borderline collective readings and is comfortable
              with unbounded sets. "each" insists on individual
              treatment and implies the set is bounded and enumerable.
              "every star in the sky" feels natural, "each star in
              the sky" implies you could list them),
              "all" (collective universal — "all" groups members together,
              "each" separates them. "all" allows and even favors
              collective verb readings, "each" forbids them),
              "both" (dual quantifier — exactly two members. "each" is
              for any size set, "both" restricts to exactly two),
              "any" (free-choice — "any" picks one indifferently,
              "each" iterates through all individually)

---

WORD: many
  type:       approximate quantifier, large
  function:   scope limiter with quantity signal — sets the following noun
              to TYPE-level, existential scope (a subset, not the full
              type), and adds a quantity signal: the subset is large
              relative to context or expectation. the claim itself is
              unchanged
  attaches:   forward to the next noun phrase (plural noun form). modifies
              the noun's scope to EXISTENTIAL / SUBSET and adds a
              quantity annotation of HIGH
  signals:    existential scope, large quantity (relative to expectations
              or context), indefinite, plural. the claim applies to a
              subset that is notably large, but "many" does not specify
              a majority
  result:     sets noun scope to TYPE / EXISTENTIAL with quantity = HIGH.
              does not produce or modify any claim. the verb's claim
              fires unchanged — "many dogs bark" → dog CAN_DO bark = True,
              applied at TYPE level with existential scope, quantity
              signal HIGH
  not:        "few" (small quantity with negative implication — opposite
              end of the quantity scale, and "few" carries evaluative
              negativity that "many" does not mirror),
              "some" (existential, quantity-neutral — "some" makes no
              assertion about how large the subset is, "many"
              specifically asserts largeness),
              "most" (majority — "most" implies more than half, "many"
              implies large quantity but not necessarily a majority),
              "all" (universal — complete type, "many" is explicitly
              a subset),
              "several" (moderate quantity — "several" implies a
              countable handful, "many" implies a notably larger number)

---

WORD: few
  type:       approximate quantifier, small, negative-evaluative
  function:   scope limiter with quantity signal and evaluative charge —
              sets the following noun to TYPE-level, existential scope,
              and adds a quantity signal: the subset is small AND smaller
              than expected or desired. the claim itself is unchanged,
              but the scope carries a negative evaluation
  attaches:   forward to the next noun phrase (plural noun form). modifies
              the noun's scope to EXISTENTIAL / SUBSET and adds a
              quantity annotation of LOW with negative evaluation
  signals:    existential scope, small quantity, negative implication
              (fewer than expected). plural. the claim applies to a
              subset that is notably small and the speaker registers
              this as insufficient or surprising
  result:     sets noun scope to TYPE / EXISTENTIAL with quantity = LOW,
              evaluation = NEGATIVE. does not produce or modify any claim.
              the verb's claim fires unchanged — "few students passed" →
              student DID pass = True, applied at TYPE level with
              existential scope, quantity signal LOW, evaluation NEGATIVE
  not:        "a few" (small quantity but POSITIVE implication — "few"
              means "not many, disappointingly," "a few" means "some,
              and that's enough." "few friends came" = disappointing
              turnout, "a few friends came" = a nice small group.
              this distinction is critical — the article "a" flips
              the evaluative charge entirely),
              "many" (large quantity — opposite end of the scale,
              no negative charge),
              "some" (existential, quantity-neutral — "some" is neutral
              about whether the quantity is satisfying, "few" signals
              it is not),
              "none" (zero — "few" is small but nonzero, "none" is zero),
              "several" (moderate, neutral — "several" carries no
              evaluative charge, "few" carries negative evaluation)
  notes:      the distinction between "few" (negative) and "a few"
              (positive) is one of the most important in English
              quantification. the presence or absence of the article
              "a" completely flips the evaluative signal. the system
              must detect "a few" as a compound unit and not parse
              "a" and "few" independently

---

WORD: any
  type:       free-choice / polarity-sensitive quantifier
  function:   scope marker whose behavior depends on clause polarity.
              in positive clauses: sets the noun to TYPE-level with
              FREE-CHOICE scope — whichever member is selected, the
              claim holds. in negative clauses: reinforces the negation
              by extending it to every possible member (not even one).
              in interrogative clauses: probes whether any member qualifies.
              the claim itself is unchanged in all cases — only the scope
              mode shifts
  attaches:   forward to the next noun phrase (singular or plural).
              modifies the noun's scope based on clause polarity
  signals:    indefinite, unrestricted selection, no preference for which
              member. polarity-sensitive: positive → FREE_CHOICE,
              negative → UNIVERSAL reinforcement of negation,
              interrogative → EXISTENTIAL probe
  result:     in positive context: sets noun scope to TYPE / FREE_CHOICE.
              the verb's claim fires unchanged — "any dog can bark" →
              dog CAN_DO bark = True, applied at TYPE level, true
              regardless of which member is selected.
              in negative context: reinforces the negation operator's
              scope to be universal — "I don't have any dogs" → the
              negation applies to every possible member, equivalent
              to "I have no dogs."
              in interrogative context: sets scope to EXISTENTIAL —
              "do you have any dogs?" → probes whether at least one
              qualifies
  not:        "some" (existential, commits to existence — "some dogs
              bark" asserts the subset exists. "any dog can bark" is
              indifferent to which one. "some" commits, "any" is open),
              "all" (universal, collective — "all" means every member
              is included as a group. "any" means whichever one you
              pick, the claim holds — similar result but different
              framing),
              "every" (distributive universal — "every" iterates through
              all members, "any" picks one arbitrarily),
              "no" (negative determiner — "no dogs" carries its own
              negation. "any" in negative context needs the negation
              operator elsewhere: "not any dogs" ≈ "no dogs" but
              "any" itself is not negative)
  notes:      "any" is polarity-sensitive — its scope mode shifts
              depending on clause polarity. the system must check
              whether the clause contains a negation operator, an
              interrogative marker, or a conditional ("if") to
              determine which mode applies. positive clause =
              FREE_CHOICE. negative clause = UNIVERSAL reinforcement
              of negation. interrogative clause = EXISTENTIAL probe.
              conditional clause ("if any dogs bark") = FREE_CHOICE
              within the conditional scope

---

WORD: who
  type:       relative/interrogative pronoun, animate, subject
  function:   dual function — (1) as interrogative: opens a question
              seeking the identity of an animate agent. (2) as relative:
              opens a relative clause that modifies the preceding
              animate noun — carries the preceding noun forward as the
              subject of the following verb phrase, producing a sub-sequence
  attaches:   as interrogative: forward to the verb of the question.
              fills the unknown subject slot.
              as relative: backward to the preceding animate noun
              (the antecedent), AND forward to the verb of the
              relative clause as its subject
  signals:    animate referent, subject case, identity-seeking (interrogative)
              or identity-linking (relative). the target must be a person
              or animate entity
  result:     as interrogative: opens an identity query —
              QUERY: IDENTIFY([subject]) WHERE [subject] DID [verb].
              "who ran?" → find the animate entity X where X DID run.
              as relative: takes the last matching animate noun, injects
              it as subject of the following verb phrase, produces a
              sub-sequence. "the man who ran" → man DID run (the relative
              clause adds a claim to the antecedent)
  not:        "whom" (same referent class but object case — "who" is the
              agent in the clause, "whom" is the patient. "who called
              you" vs "whom did you call"),
              "which" (non-animate or selection-from-set — "who" is for
              people/animate entities, "which" is for things or for
              choosing among a defined set),
              "what" (open-ended identity query for things — "who"
              restricts to animate, "what" is for inanimate or
              category-level questions),
              "that" as relative pronoun (neutral — "that" can replace
              "who" in restrictive relatives but carries no animacy
              signal and cannot be used in non-restrictive relatives)

---

WORD: whom
  type:       relative/interrogative pronoun, animate, object
  function:   dual function — (1) as interrogative: opens a question
              seeking the identity of an animate patient or recipient.
              (2) as relative: opens a relative clause with the pronoun
              filling the object slot of the embedded clause
  attaches:   as interrogative: forward to the verb of the question.
              fills the unknown object slot.
              as relative: backward to the preceding animate noun
              (the antecedent), AND forward into the relative clause
              as its object
  signals:    animate referent, object case, identity-seeking (interrogative)
              or identity-linking (relative). the target is acted upon,
              not acting
  result:     as interrogative: opens an identity query —
              QUERY: IDENTIFY([object]) WHERE [subject] ACTED_ON [object].
              "whom did you see?" → find the animate entity X where
              ADDRESSEE ACTED_ON X.
              as relative: links the antecedent as object of the
              relative clause — "the man whom I called" → SPEAKER
              DID call man
  not:        "who" (same referent class but subject case — "who" is the
              agent, "whom" is the patient. "who saw you" vs
              "whom did you see"),
              "which" (non-animate — "whom" is for people, "which" is
              for things or defined-set selection),
              "that" as relative pronoun (neutral and can replace "whom"
              in restrictive clauses, but "that" has no case marking
              and no animacy signal)
  notes:      "whom" is declining in informal English and is frequently
              replaced by "who" in both interrogative and relative uses.
              the system should recognize "who" in object position as
              a variant of "whom" rather than an error. "whom" should
              be preferred for parsing precision but "who" in object
              position should resolve identically

---

WORD: which
  type:       relative/interrogative pronoun, selective
  function:   dual function — (1) as interrogative: opens a question
              seeking selection from a defined or implied set.
              (2) as relative: opens a relative clause modifying
              the preceding noun, typically non-animate or when
              choosing among identified alternatives
  attaches:   as interrogative: forward to the noun being selected from,
              or directly to the verb if the noun is implied.
              "which book?" → select from the set of books.
              as relative: backward to the preceding noun (antecedent),
              AND forward into the relative clause as subject or object
  signals:    selection from a defined set, typically non-animate (but
              can be animate when choosing among identified individuals).
              implies that the set of options exists and the question
              is about choosing among them, not identifying from scratch
  result:     as interrogative: opens a selection query —
              QUERY: SELECT([noun]) FROM [defined set].
              "which car is yours?" → select from the known set of cars.
              as relative: takes the preceding noun, injects it into the
              relative clause, produces a sub-sequence.
              "the car which broke down" → car DID break_down
  not:        "who/whom" (animate-specific — "which" is typically
              non-animate or selection-focused, "who" is for
              people without a predefined set. "which doctor do you
              see" = choose from your options, "who is your doctor"
              = identify the person),
              "what" (open-ended — "what" asks with no predefined set,
              "which" asks with an implied or stated set.
              "what book should I read" = open field,
              "which book should I read" = from these options),
              "that" as relative pronoun (restrictive only — "which" can
              introduce both restrictive and non-restrictive relatives.
              "the book that I read" = restrictive, "the book, which
              I read" = non-restrictive. "that" cannot do the second)
  notes:      in non-restrictive relative clauses (set off by commas),
              "which" is required — "that" cannot substitute.
              "the car, which was red, broke down" is valid.
              "the car, that was red, broke down" is not. the presence
              of commas around the relative clause is the primary
              signal for non-restrictive reading

---

WORD: that (relative pronoun)
  type:       relative pronoun, neutral, restrictive
  function:   restrictive clause linker — opens a relative clause that
              narrows or defines the preceding noun. the relative clause
              is essential to identifying which instance of the noun
              is meant. "that" is neutral regarding animacy and case.
              carries the preceding noun forward as subject of the
              following verb phrase, producing a sub-sequence
  attaches:   backward to the preceding noun (antecedent), AND forward
              into the relative clause. "that" can fill the subject
              or object slot within the relative clause depending on
              clause structure
  signals:    restrictive modification (the clause is essential for
              identification), neutral animacy (works for people and
              things), neutral case (can be subject or object of the
              relative clause). carries no additional information
              beyond linking
  result:     takes the preceding noun, injects it into the relative
              clause, produces a sub-sequence. the relative clause's
              claim becomes a defining property of the antecedent noun.
              "the dog that barked" → dog DID bark (this claim narrows
              which dog is meant). the antecedent is only fully
              identified once the relative clause resolves
  not:        "that" as determiner (demonstrative — "that dog" points
              to a specific instance at a distance. "that" as relative
              pronoun introduces a clause, not a noun phrase.
              position is the disambiguator: if followed by a noun, it's
              a determiner; if followed by a clause, it's a relative
              pronoun),
              "which" (can be restrictive or non-restrictive — "that" is
              restrictive only. "the car that broke" = defines which
              car. "the car, which broke" = adds extra info about an
              already-identified car. "that" cannot do the second),
              "who" (animate-specific and can be non-restrictive — "that"
              is neutral on animacy and strictly restrictive. "the man
              who arrived" and "the man that arrived" are both valid,
              but "the man, who arrived" is valid while "the man, that
              arrived" is not),
              "which" as interrogative (asks a question — "that" as
              relative pronoun never asks questions, only links clauses)
  notes:      "that" as relative pronoun is often omittable when it
              fills the object slot of the relative clause. "the book
              that I read" and "the book I read" are equivalent.
              when "that" fills the subject slot, it cannot be omitted:
              "the dog that barked" is valid, "the dog barked" changes
              meaning entirely. the system should detect zero-relative
              constructions (missing "that" in object relatives) and
              reconstruct the implied "that"

---

## Group 6: Conjunctions & Prepositions

WORD: and
  type:       coordinating conjunction
  function:   additive connector — links two elements of the same type
              (two nouns, two verbs, two clauses) into a compound
              structure. both sides are equally true and equally weighted
  attaches:   backward to the preceding element AND forward to the
              following element. both must be the same grammatical type
              (noun+noun, verb+verb, clause+clause)
  signals:    addition, co-occurrence, equal weight. no contrast, no
              conditionality, no causation
  result:     duplicates the surrounding structure for both elements.
              "the dog is big and fast" → dog HAS_PROPERTY big,
              dog HAS_PROPERTY fast (both fire independently).
              "jaimee ran and jumped" → jaimee DID run, jaimee DID jump
              (both fire independently with shared subject)
  not:        "but" (contrastive — signals that the second element is
              unexpected given the first. "big but slow" implies big
              things are usually not slow),
              "or" (alternative — only one of the two, not both),
              "then" (sequential — implies ordering. "and" has no
              inherent ordering unless context adds it),
              "also" (additive like "and" but operates across sentences
              rather than within a compound structure)

---

WORD: or
  type:       coordinating conjunction, disjunctive
  function:   alternative connector — links two elements of the same type
              but marks them as alternatives. only one is selected, active,
              or true at a time. creates a branch, not a compound
  attaches:   backward to the preceding element AND forward to the
              following element. both must be the same grammatical type
  signals:    disjunction, alternative, mutual exclusivity (default).
              one or the other, not both. in some contexts can be
              inclusive ("do you want cream or sugar" can mean either
              or both), but default is exclusive
  result:     creates a BRANCH over the two elements. "the dog is big
              or small" → dog HAS_PROPERTY big OR dog HAS_PROPERTY small
              (only one fires, selection deferred to context). does not
              duplicate — it forks
  not:        "and" (additive — both sides are true. "or" selects one),
              "nor" (negative disjunction — "or" is neutral, "nor"
              presupposes both are rejected. "not X nor Y" = neither),
              "either" (often paired with "or" as a frame marker —
              "either" signals that a disjunction is coming, but "or"
              is the actual connector),
              "otherwise" (conditional alternative — "otherwise" implies
              consequence of not acting, "or" simply presents options)
  notes:      inclusive vs exclusive "or" is a genuine ambiguity.
              "would you like tea or coffee" is typically exclusive
              (pick one). "applicants with experience or a degree may
              apply" is typically inclusive (either or both qualifies).
              the system should default to exclusive and flag when
              context suggests inclusive

---

WORD: but
  type:       coordinating conjunction, contrastive
  function:   contrastive connector — links two elements but marks the
              second as unexpected, surprising, or in tension with the
              first. both sides are true, but they pull in different
              directions
  attaches:   backward to the preceding element AND forward to the
              following element. same grammatical type requirement as "and"
  signals:    contrast, unexpectedness, tension. the second element
              partially undermines, qualifies, or complicates the first.
              pragmatic weight falls on the second element — what comes
              after "but" is what the speaker considers more important
  result:     both claims fire (like "and"), but the claim pair is
              annotated {contrastive: true, pair: [claim_A, claim_B]}.
              "the dog is big but gentle" → dog HAS_PROPERTY big,
              dog HAS_PROPERTY gentle, with contrastive annotation on
              the pair. the annotation is pragmatic metadata, not a
              relation between the property nodes
  not:        "and" (purely additive — no tension or surprise implied),
              "however" (same contrastive function but operates between
              sentences, not within a compound structure. "but" is
              intra-sentence, "however" is inter-sentence),
              "yet" (very close to "but" — slightly more emphatic
              surprise. "but" marks contrast, "yet" marks that the
              contrast is particularly striking),
              "although/though" (concessive — sets up the unexpected
              element first rather than second. "although it was big,
              it was gentle" vs "it was big but gentle")
  notes:      "but" can occasionally function as "except" — "everyone
              but jaimee left" means everyone except jaimee. in this
              usage it functions as an exclusion operator (REJECTS
              membership for the named entity) on the preceding set,
              not a contrastive conjunction. the system should check
              whether "but" follows a quantifier or universal set

---

WORD: if
  type:       subordinating conjunction, conditional
  function:   condition marker — introduces a clause whose truth is a
              prerequisite for the main clause. creates a conditional
              dependency: the main clause's claim only fires when the
              condition clause is true
  attaches:   forward to the following clause (the condition), and
              connects that clause to the main clause (the consequent).
              the main clause may follow ("if X, then Y") or precede
              ("Y if X")
  signals:    conditionality, hypotheticality, dependency. the condition
              clause is not asserted as true — it is proposed as a
              scenario. the main clause is asserted only within that
              scenario
  result:     [main clause claim] REQUIRES [condition clause] = True.
              the main clause's claim is wrapped in a conditional: it
              fires only if the condition resolves to true.
              "if it rains, I will stay" → I DID stay = FUTURE,
              REQUIRES(rain = True)
  not:        "when" (temporal, not conditional — "when" presupposes the
              event will happen and asks about timing. "if" leaves the
              event uncertain),
              "whether" (introduces alternatives for evaluation —
              "I don't know whether it will rain" is not a condition,
              it's an open question),
              "because" (causal — "because" asserts that one thing
              caused another. "if" does not assert causation, only
              dependency),
              "unless" (negative conditional — "unless" means "if not".
              "unless it rains, I will go" = "if it does not rain,
              I will go")

---

WORD: then
  type:       sequential/consequential adverb
  function:   sequence or consequence marker — marks the following element
              as occurring after the preceding element in time, or as the
              result/consequent of a prior condition. signals ordering
              or entailment
  attaches:   backward to the preceding clause or event AND forward to
              the following clause or event. links them in a sequence or
              conditional chain
  signals:    temporal sequence ("first X, then Y") or logical consequence
              ("if X, then Y"). in temporal mode, establishes ordering.
              in consequential mode, marks the second clause as dependent
              on the first
  result:     temporal: stores a BEFORE edge from the preceding event to
              the following event. "she ate, then left" → eat BEFORE leave.
              consequential (paired with "if"): REQUIRES — the consequent
              fires only when the antecedent is true. "if...then" is
              logical dependency, not temporal sequence
  not:        "and" (additive, no ordering — "and" treats both elements
              as co-equal and simultaneous by default. "then" imposes
              sequence),
              "therefore" (logical entailment — "therefore" asserts that
              the second follows logically and necessarily from the first.
              "then" can be merely temporal without logical force),
              "next" (purely temporal — "next" is always about ordering,
              never about logical consequence),
              "so" (consequence — "so" implies a causal connection,
              "then" in temporal mode implies only ordering)

---

WORD: because
  type:       subordinating conjunction, causal
  function:   causal connector — marks the following clause as the reason
              or cause for the preceding clause. establishes a directional
              causal relationship: the "because" clause explains why the
              main clause is true
  attaches:   backward to the preceding main clause AND forward to the
              following reason clause. the reason clause is subordinate —
              it explains the main clause, not the other way around
  signals:    causation, reason, explanation. the speaker asserts that the
              reason clause is the direct cause of the main clause being
              true
  result:     stores a CAUSES edge from the reason clause to the main
              clause. "the ground is wet because it rained" → rain CAUSES
              ground HAS_PROPERTY wet. the word "because" presents the
              effect first and the cause second, but the stored edge
              points from cause to effect. querying backward from the
              effect through the CAUSES edge yields the "caused by"
              reading
  not:        "so" (consequential — same causal link, reversed
              presentation order. "it rained so the ground is wet"
              presents cause first. both store the same CAUSES edge
              from rain to wet ground),
              "since" (causal or temporal — "since" can mean "because"
              but also "from the time that." "because" is unambiguously
              causal),
              "if" (conditional, not causal — "if" proposes a
              hypothetical dependency via REQUIRES. "because" asserts
              an actual causal link via CAUSES),
              "therefore" (logical entailment — "therefore" signals
              deduction. "because" signals explanation. they can
              co-occur but operate differently)

---

WORD: so
  type:       conjunctive adverb / subordinating conjunction, consequential
  function:   consequence marker — marks the following clause as the result
              or outcome of the preceding clause. can also function as an
              intensifier ("so big") or purpose marker ("so that")
  attaches:   backward to the preceding clause (cause) AND forward to the
              following clause (consequence). in intensifier mode, forward
              to the following adjective/adverb
  signals:    consequence (primary): the second clause results from the
              first. intensifier: degree amplification. purpose: the first
              clause is done in order to achieve the second
  result:     consequence: stores a CAUSES edge from the preceding clause
              to the following clause. "it rained so the ground is wet" →
              rain CAUSES ground HAS_PROPERTY wet. same edge as "because"
              would produce, just presented in cause-first order.
              intensifier: HAS_PROPERTY [adjective], degree = HIGH.
              "so big" → big with amplified degree.
              purpose (with "that"): [clause A] REQUIRES [clause B] as goal
  not:        "because" (same causal link, reversed presentation order —
              "because" presents effect first then cause, "so" presents
              cause first then effect. both store the same CAUSES edge),
              "therefore" (formal logical entailment — "therefore" is more
              formal and explicitly deductive, "so" is conversational and
              can be causal without strict logical necessity),
              "then" (sequential or consequential — "then" can be purely
              temporal via BEFORE, "so" always implies causal connection
              via CAUSES),
              "very" (intensifier — when "so" intensifies, it is close
              to "very" but often carries emotional emphasis or implies
              a consequence: "so big that...")
  notes:      the three functions (consequence, intensifier, purpose) are
              structurally quite different. consequence "so" stores a
              CAUSES edge. intensifier "so" modifies a property's degree.
              purpose "so that" stores a REQUIRES edge. the system should
              disambiguate by checking what follows: clause → consequence,
              adjective → intensifier, "that" + clause → purpose

---

WORD: yet
  type:       coordinating conjunction, contrastive-emphatic / temporal adverb
  function:   emphatic contrast or temporal marker — as conjunction,
              functions like "but" with additional emphasis that the
              contrast is surprising or noteworthy. as adverb, signals
              "up to this point in time"
  attaches:   conjunction mode: backward to the preceding element AND
              forward to the following element (same as "but").
              adverb mode: modifies the verb of the current clause,
              scoping it to the present moment
  signals:    conjunction: strong contrast, surprise, persistence despite
              expectation. adverb: temporal scope up to now, often with
              implied expectation of change
  result:     conjunction: both claims fire, claim pair annotated
              {contrastive: true, emphatic: true, pair: [claim_A, claim_B]}.
              stronger than "but" — the speaker marks the contrast as
              striking.
              adverb: [subject] DID [verb] = False, tense = PRESENT,
              with implied expectation of future change. "he hasn't
              arrived yet" → arrived = False, but the system should
              note the expectation that this will become True
  not:        "but" (contrastive without the emphatic charge — "but"
              marks simple contrast, "yet" marks surprising or
              remarkable contrast),
              "still" (temporal continuity — "still" means the state
              persists. "yet" in adverb mode means the state hasn't
              begun. "he's still here" vs "he hasn't arrived yet"),
              "however" (inter-sentence contrastive — "however" connects
              across sentence boundaries, "yet" operates within or at
              the boundary),
              "already" (temporal, opposite polarity — "already" means
              sooner than expected, "yet" in adverb mode means not so
              far but expected)

---

WORD: in
  type:       spatial/temporal preposition, containment
  function:   containment marker — locates the subject or action inside
              the boundaries of the following noun. signals interiority
  attaches:   backward to the preceding noun or verb AND forward to the
              following noun (the container/frame). "the cat in the box" →
              cat LOCATED box. "she arrived in May" → arrival LOCATED May
  signals:    containment, enclosure, bounded location. spatial: within
              the boundaries of. temporal: within a time period. abstract:
              within a domain ("in mathematics", "in trouble")
  result:     [subject/action] LOCATED [container] = True, MODE = INTERIOR.
              the located entity is within the boundaries of the container,
              not on its surface, not adjacent to it
  not:        "on" (surface contact, not containment — "on the table" is
              on top, "in the table" is inside. different spatial
              relationship),
              "at" (point location, not containment — "at the store"
              treats the store as a point. "in the store" treats it as
              a bounded volume the subject is inside),
              "into" (directional containment — "into" implies motion
              toward the interior. "in" is static, already inside),
              "within" (near-synonym — "within" is more formal and
              emphasizes the boundary. functionally equivalent in
              most contexts)

---

WORD: on
  type:       spatial/temporal preposition, surface contact
  function:   surface marker — locates the subject in contact with the
              exterior surface of the following noun
  attaches:   backward to the preceding noun or verb AND forward to the
              following noun (the surface). "the book on the table" →
              book LOCATED table, MODE = SURFACE
  signals:    surface contact, support, adjacency to exterior. spatial:
              resting upon. temporal: on a specific date ("on Monday").
              abstract: concerning a topic ("a book on physics")
  result:     [subject/action] LOCATED [surface] = True, MODE = SURFACE.
              the located entity is in contact with the exterior of the
              reference object, supported by it
  not:        "in" (containment — "in" is interior, "on" is surface.
              "in the box" vs "on the box"),
              "at" (point location — "at the table" treats the table as
              a meeting point. "on the table" specifies the physical
              surface),
              "upon" (formal synonym — functionally identical to "on"
              in most contexts),
              "above" (vertical proximity without contact — "above the
              table" is elevated but not touching, "on the table"
              requires contact)

---

WORD: at
  type:       spatial/temporal preposition, point location
  function:   point marker — locates the subject at a specific point in
              space, time, or abstraction. treats the location as a
              dimensionless point regardless of actual size
  attaches:   backward to the preceding noun or verb AND forward to the
              following noun (the point). "she is at the store" →
              she LOCATED store, MODE = POINT
  signals:    point location, precise position. spatial: at a specific
              place. temporal: at a specific time ("at noon"). abstract:
              at a state ("at war", "at ease")
  result:     [subject/action] LOCATED [point] = True, MODE = POINT.
              the entity is co-located with the reference point. no
              information about interior/exterior or surface
  not:        "in" (containment — "in the store" means inside the
              boundaries. "at the store" is positional, agnostic about
              interior/exterior),
              "on" (surface — "on the store" would mean on top of it.
              "at the store" is positional),
              "to" (directional — "to the store" implies motion toward.
              "at the store" implies already there),
              "by" (proximity — "by the store" means near it. "at the
              store" means co-located with it)

---

WORD: to
  type:       directional preposition / infinitive marker
  function:   direction or purpose marker — as preposition, marks the
              following noun as the destination or recipient of motion
              or transfer. as infinitive marker, marks the following
              verb as a purpose, intention, or unconjugated action
  attaches:   preposition mode: backward to the preceding verb of motion
              or transfer AND forward to the following noun
              (destination/recipient). infinitive mode: forward to the
              following verb
  signals:    preposition: directionality, destination, recipient.
              something moves toward or is given to the target.
              infinitive: purpose, intention, or verb in base form
              ("to run", "to see")
  result:     preposition: [subject] ACTED_ON [destination/recipient].
              "she went to the store" → she DID go, LOCATED store
              (destination). "he gave it to her" → he ACTED_ON her,
              MODE = RECIPIENT.
              infinitive: marks following verb as PURPOSE or
              UNCONJUGATED_ACTION. "she wants to run" → she CAN_DO run,
              MODE = DESIRED
  not:        "toward" (directional but without arrival — "toward the
              store" implies heading in that direction without
              necessarily reaching it. "to the store" implies arrival
              or intended arrival),
              "for" (beneficiary or purpose — "for her" marks benefit,
              "to her" marks destination/recipient. "a gift for her"
              vs "give it to her"),
              "at" (point location, static — "at" is already there.
              "to" implies motion toward),
              "into" (directional + containment — "into" specifies
              entering the interior. "to" is direction only)
  notes:      the preposition and infinitive marker are structurally
              unrelated functions sharing a surface form. the system
              disambiguates by checking what follows: noun → preposition,
              verb → infinitive marker

---

WORD: from
  type:       directional preposition, origin/source
  function:   source marker — marks the following noun as the origin,
              starting point, or source from which the subject or action
              departs. the directional inverse of "to"
  attaches:   backward to the preceding verb or noun AND forward to the
              following noun (the source/origin). "she came from Paris" →
              she DID come, LOCATED Paris (origin)
  signals:    origin, source, departure point. spatial: starting location.
              temporal: starting time ("from Monday"). abstract: source
              or cause ("from experience")
  result:     [subject/action] LOCATED [source], MODE = ORIGIN.
              "she is from France" → she LOCATED France, MODE = ORIGIN.
              "he ran from the bear" → he DID run, LOCATED bear
              (origin/departure)
  not:        "to" (destination — "from" marks the starting point, "to"
              marks the endpoint. directional opposites),
              "of" (possession or composition — "from" implies departure
              or derivation. "of" implies belonging or constitution.
              "a man from France" = origin, "a man of France" = belonging),
              "by" (agent or means — "from" marks source, "by" marks
              agent or method. "a letter from her" = sent by her,
              "a letter by her" = authored by her),
              "since" (temporal origin with continuation — "since Monday"
              implies from Monday until now. "from Monday" can start
              Monday without implying continuation to present)

---

WORD: with
  type:       comitative/instrumental preposition
  function:   accompaniment or instrument marker — marks the following noun
              as either accompanying the subject or the instrument/means
              used to perform the action
  attaches:   backward to the preceding noun or verb AND forward to the
              following noun (the companion/instrument). "she walked with
              her friend" → companion. "he cut it with a knife" → instrument
  signals:    accompaniment (comitative): the subject and the companion
              are together. instrument (instrumental): the tool or means.
              attribute: a descriptive feature ("a man with a hat")
  result:     comitative: [subject] DID [verb] with [companion]
              (co-participation).
              instrumental: [subject] DID [verb], REQUIRES [instrument]
              (the instrument was necessary for the action).
              attributive: [subject] HAS_FEATURE [attribute].
              "a dog with spots" → dog HAS_FEATURE spots
  not:        "by" (agent or means — "by" marks the agent of a passive
              construction or a general means. "with" marks the specific
              tool or companion. "cut by a knife" → knife is agent.
              "cut with a knife" → knife is instrument used by someone),
              "and" (conjunction — "she and her friend walked" makes them
              equal co-subjects. "she walked with her friend" makes her
              the subject and the friend the accompaniment),
              "using" (instrumental only — "using" is always instrumental,
              never comitative. "with" can be either),
              "without" (negation of "with" — absence of accompaniment
              or instrument)

---

WORD: of
  type:       genitive/partitive preposition
  function:   relation marker — connects two nouns where the second noun
              specifies a possessive, compositional, partitive, or
              descriptive relationship to the first. the most abstract
              and multifunctional preposition
  attaches:   backward to the preceding noun AND forward to the following
              noun. "the color of the sky" → color PART_OF sky.
              "a cup of tea" → cup contains tea
  signals:    possession, composition, partition, description, origin.
              the specific relation depends on the semantic types of
              the two nouns
  result:     default: [noun A] PART_OF [noun B].
              "the roof of the house" → roof PART_OF house.
              "a cup of water" → water PART_OF cup (contents).
              descriptive: [noun A] HAS_PROPERTY [noun B].
              "a man of courage" → man HAS_PROPERTY courage.
              origin: [noun A] LOCATED [noun B], MODE = ORIGIN.
              "people of France" → people LOCATED France, MODE = ORIGIN
  not:        "from" (origin with departure — "of" can mark origin but
              without the motion sense. "people of France" = belonging.
              "people from France" = origin/departure),
              "'s" (possessive — functionally similar but syntactically
              different. "the man's dog" = "the dog of the man"),
              "with" (accompaniment/attribute — "a man with courage"
              implies the attribute is carried, "a man of courage"
              implies it is inherent),
              "about" (topic — "a book of poems" = contains poems.
              "a book about poems" = discusses poems as topic)
  notes:      "of" is the most overloaded preposition in English.
              disambiguation priority: partition ("some of") >
              possession ("the hat of") > composition ("a cup of") >
              description ("a man of") > origin ("people of").
              check the first noun's semantics to select

---

WORD: by
  type:       agentive/spatial preposition
  function:   agent or proximity marker — marks the following noun as
              the agent performing an action (especially in passive
              constructions), the means or method, or spatial proximity
  attaches:   backward to the preceding verb (agent/means) or noun
              (proximity) AND forward to the following noun.
              "the cake was baked by her" → agent. "travel by train" →
              means. "sit by the window" → proximity
  signals:    agent (passive): who performed the action. means: the
              method or channel. proximity: near, beside
  result:     agent: [subject] ACTED_ON BY [agent]. "the ball was kicked
              by the boy" → boy ACTED_ON ball (agent extraction from
              passive — the stored edge points from agent to patient).
              means: [subject] DID [verb], REQUIRES [means].
              "travel by train" → travel REQUIRES train (as method).
              proximity: [subject] LOCATED [reference], MODE = ADJACENT
  not:        "with" (instrument — "with" marks a specific tool held or
              used, "by" marks the agent or general method. "cut with
              a knife" = specific tool. "killed by a knife" = the knife
              is the agent in passive voice),
              "from" (source/origin — "by" in agent mode identifies who
              did it, "from" identifies where it came from),
              "near" (proximity only — "near" is purely spatial proximity.
              "by" in proximity mode is similar but also carries a sense
              of alongside/beside),
              "through" (means with passage — "by" is a method marker,
              "through" implies process. "by hard work" vs "through
              hard work")

---

WORD: for
  type:       benefactive/purposive preposition
  function:   beneficiary, purpose, or duration marker — marks the
              following noun as the beneficiary of the action, the purpose
              or reason, or the duration of time
  attaches:   backward to the preceding verb or noun AND forward to the
              following noun. "a gift for you" → beneficiary.
              "tools for cutting" → purpose. "waited for hours" → duration
  signals:    beneficiary: who benefits. purpose: the goal or intended use.
              duration: the span of time. exchange: what is traded
              ("paid ten dollars for it")
  result:     beneficiary: [subject] DID [verb], ACTED_ON [recipient]
              (beneficiary). "she baked a cake for him" → she DID bake,
              ACTED_ON him (as beneficiary).
              purpose: [noun/action] REQUIRES [purpose] as goal.
              "a tool for cutting" → tool REQUIRES cutting as PURPOSE.
              duration: [action] LOCATED [time span] (temporal frame).
              "waited for two hours" → wait LOCATED two_hours
              (temporal containment)
  not:        "to" (recipient/direction — "for" marks beneficiary, "to"
              marks direct recipient. "I baked a cake for her" = she
              benefits. "I gave the cake to her" = she receives directly),
              "because" (causal — "because" explains why something
              happened via CAUSES. "for" as purpose explains what
              something is intended to achieve — forward-looking),
              "during" (temporal containment — "during the meeting" =
              within the meeting's time. "for the meeting" = purpose
              or beneficiary of the meeting),
              "since" (temporal origin — "since Tuesday" marks the start
              point. "for three days" marks the duration without
              specifying start)

---

WORD: about
  type:       topical/approximative preposition
  function:   topic or approximation marker — marks the following noun as
              the subject matter of the preceding element, or as an
              approximate quantity
  attaches:   backward to the preceding noun or verb AND forward to the
              following noun. "a book about dogs" → topic. "about fifty
              people" → approximation
  signals:    topic: the following noun is what the preceding element
              concerns or discusses. approximation: the following
              quantity is not exact
  result:     topic: [noun/action] HAS_FEATURE topic = [following noun].
              "a book about dogs" → book HAS_FEATURE topic = dogs.
              "she talked about the plan" → talk ACTED_ON plan,
              MODE = TOPIC.
              approximation: modifies the precision of the following
              number. the value is approximate, not exact
  not:        "of" (composition or possession — "a book of poems" =
              contains poems. "a book about poems" = discusses poems
              as topic. "of" is structural, "about" is topical),
              "on" (topic in formal register — "a paper on quantum
              physics" is functionally identical to "a paper about
              quantum physics." "on" is slightly more formal/academic),
              "around" (approximation synonym — "around fifty" is
              functionally equivalent to "about fifty." "around" also
              has spatial meanings "about" lacks),
              "concerning/regarding" (formal topic markers — functionally
              identical to topical "about" but higher register)

---

WORD: than
  type:       comparative preposition/conjunction
  function:   comparison anchor — marks the following noun or clause as
              the reference point against which the preceding element is
              compared. requires a comparative marker (adjective + -er,
              "more", "less") in the preceding element
  attaches:   backward to the preceding comparative element AND forward
              to the following noun or clause (the comparand)
  signals:    comparison, relative measure. the preceding element has been
              marked as comparative and "than" provides the anchor
  result:     [subject] HAS_PROPERTY [property] gt [comparand] (for
              "more"/"bigger"/"-er") or lt [comparand] (for "less"/
              "smaller"). "she is taller than him" → she HAS_PROPERTY
              tall gt him. the comparator (gt, lt) is determined by
              the comparative word
  not:        "as" (equality comparison — "as tall as him" compares for
              equality via eq. "taller than him" compares for inequality
              via gt/lt. "than" always implies a difference),
              "then" (sequential/consequential — entirely different
              function despite near-identical pronunciation. "than"
              compares, "then" sequences via BEFORE),
              "from" (difference marker in some constructions —
              "different from" is standard, "different than" is
              informal variant)

---

WORD: as
  type:       comparative/role preposition / temporal conjunction
  function:   equality comparison, role assignment, or temporal
              co-occurrence marker
  attaches:   comparison: backward to the first "as" or comparative
              context AND forward to the following noun.
              role: forward to the following noun.
              temporal: forward to the following clause
  signals:    comparison: equality of degree. role: the subject functions
              in the capacity of the following noun. temporal: two events
              occur simultaneously
  result:     comparison: [subject] HAS_PROPERTY [adjective] eq [comparand].
              "as fast as a cheetah" → speed eq cheetah.
              role: [subject] IS_A [role], MODE = FUNCTIONAL.
              "she works as a doctor" → she IS_A doctor (functional
              capacity, not necessarily permanent identity).
              temporal: stores a SIMULTANEOUS_WITH edge between the
              two events. "as the sun set, she left" → sunset
              SIMULTANEOUS_WITH departure. symmetric — no directionality,
              no causal implication
  not:        "than" (inequality comparison — "than" marks difference
              via gt/lt, "as...as" marks parity via eq),
              "like" (similarity — "like" marks resemblance or metaphor.
              "as" in comparison marks equality of a specific measurable
              property. "fast like a cheetah" = resemblance. "as fast
              as a cheetah" = measured equality),
              "because/since" (causal — "as" in temporal mode marks
              simultaneous occurrence via SIMULTANEOUS_WITH, not
              causation via CAUSES. causation may be implied but is
              not asserted),
              "while" (temporal overlap — "while" marks duration overlap.
              "as" marks the moment of co-occurrence. very close, but
              "as" is more punctual and "while" is more durative)
  notes:      "as" is highly polysemous. disambiguation priority:
              if preceded by another "as" or a degree word → comparison.
              if followed by a noun and preceded by a verb of function
              (works, serves, acts) → role. if followed by a clause →
              temporal. the system should check these in order
