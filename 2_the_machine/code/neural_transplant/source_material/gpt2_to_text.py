"""
GPT-2 → Text for Isaac Ingestion
==================================

Loads GPT-2 and writes every neuron as a text line:
    neuron_name weight0 weight1 weight2 ... function_type

That's it. Feed the output through Isaac's front door.

Usage:
    python gpt2_to_text.py                    # all components
    python gpt2_to_text.py --component attn   # attention only
    python gpt2_to_text.py --layer 0          # layer 0 only
    python gpt2_to_text.py --component embed  # embeddings only
    python gpt2_to_text.py --top-k-embed 1000 # top 1000 tokens only
    python gpt2_to_text.py --precision 3      # 3 decimal places
"""

import argparse
import sys
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer


def write_matrix_rows(f, name_prefix, matrix, function_label, precision):
    """Write each row of a matrix as one text line."""
    fmt = f"{{:.{precision}f}}"
    for row_idx in range(matrix.shape[0]):
        row = matrix[row_idx]
        weights_str = ' '.join(fmt.format(v) for v in row.tolist())
        f.write(f"{name_prefix}.n{row_idx} {weights_str} {function_label}\n")


def write_vector(f, name_prefix, vector, function_label, precision):
    """Write a 1D vector (bias, layer norm) as one text line."""
    fmt = f"{{:.{precision}f}}"
    weights_str = ' '.join(fmt.format(v) for v in vector.tolist())
    f.write(f"{name_prefix} {weights_str} {function_label}\n")


def export_embeddings(f, model, tokenizer, precision, top_k=None):
    """Token and position embeddings."""
    wte = model.transformer.wte.weight.detach()  # (vocab, 768)
    wpe = model.transformer.wpe.weight.detach()  # (1024, 768)
    fmt = f"{{:.{precision}f}}"

    # Token embeddings
    if top_k:
        # Get most common tokens by index (lower indices = more common in GPT-2)
        indices = list(range(min(top_k, wte.shape[0])))
    else:
        indices = list(range(wte.shape[0]))

    for idx in indices:
        token_str = tokenizer.decode([idx]).strip().replace(' ', '_').replace('\n', '\\n')
        if not token_str:
            token_str = f"tok{idx}"
        row = wte[idx]
        weights_str = ' '.join(fmt.format(v) for v in row.tolist())
        f.write(f"embed.token.{token_str} {weights_str} embedding\n")

    # Position embeddings
    for pos_idx in range(wpe.shape[0]):
        row = wpe[pos_idx]
        weights_str = ' '.join(fmt.format(v) for v in row.tolist())
        f.write(f"embed.pos.{pos_idx} {weights_str} positional\n")


def export_layer(f, model, layer_idx, precision):
    """All components of one transformer layer."""
    block = model.transformer.h[layer_idx]
    L = f"layer{layer_idx}"

    # Layer norm 1
    write_vector(f, f"{L}.ln1.weight", block.ln_1.weight.detach(), "layernorm", precision)
    write_vector(f, f"{L}.ln1.bias", block.ln_1.bias.detach(), "layernorm_bias", precision)

    # Attention: c_attn is (768, 2304) — Q, K, V concatenated
    # GPT-2 Conv1D: weight is (in_features, out_features)
    c_attn_w = block.attn.c_attn.weight.detach()  # (768, 2304)
    c_attn_b = block.attn.c_attn.bias.detach()     # (2304,)

    # Split into Q, K, V per head
    n_heads = 12
    head_dim = 64
    q_w, k_w, v_w = c_attn_w.split(768, dim=1)  # each (768, 768)

    for head_idx in range(n_heads):
        h_start = head_idx * head_dim
        h_end = h_start + head_dim

        q_head = q_w[:, h_start:h_end]  # (768, 64)
        k_head = k_w[:, h_start:h_end]
        v_head = v_w[:, h_start:h_end]

        # Each row = one input dimension's projection into this head
        write_matrix_rows(f, f"{L}.attn.head{head_idx}.query", q_head, "query softmax", precision)
        write_matrix_rows(f, f"{L}.attn.head{head_idx}.key", k_head, "key softmax", precision)
        write_matrix_rows(f, f"{L}.attn.head{head_idx}.value", v_head, "value linear", precision)

    # Attention bias (one line per head's Q, K, V)
    q_b, k_b, v_b = c_attn_b.split(768)
    for head_idx in range(n_heads):
        h_start = head_idx * head_dim
        h_end = h_start + head_dim
        write_vector(f, f"{L}.attn.head{head_idx}.query.bias", q_b[h_start:h_end], "query_bias", precision)
        write_vector(f, f"{L}.attn.head{head_idx}.key.bias", k_b[h_start:h_end], "key_bias", precision)
        write_vector(f, f"{L}.attn.head{head_idx}.value.bias", v_b[h_start:h_end], "value_bias", precision)

    # Attention output projection
    c_proj_w = block.attn.c_proj.weight.detach()  # (768, 768)
    c_proj_b = block.attn.c_proj.bias.detach()
    # Split by head: rows h*64:(h+1)*64 are head h's output
    for head_idx in range(n_heads):
        h_start = head_idx * head_dim
        h_end = h_start + head_dim
        write_matrix_rows(f, f"{L}.attn.head{head_idx}.output", c_proj_w[h_start:h_end, :], "attention_output linear", precision)
    write_vector(f, f"{L}.attn.output.bias", c_proj_b, "attention_output_bias", precision)

    # Layer norm 2
    write_vector(f, f"{L}.ln2.weight", block.ln_2.weight.detach(), "layernorm", precision)
    write_vector(f, f"{L}.ln2.bias", block.ln_2.bias.detach(), "layernorm_bias", precision)

    # MLP
    c_fc_w = block.mlp.c_fc.weight.detach()    # (768, 3072)
    c_fc_b = block.mlp.c_fc.bias.detach()       # (3072,)
    c_proj_w = block.mlp.c_proj.weight.detach() # (3072, 768)
    c_proj_b = block.mlp.c_proj.bias.detach()    # (768,)

    write_matrix_rows(f, f"{L}.mlp.up", c_fc_w, "gelu", precision)
    write_vector(f, f"{L}.mlp.up.bias", c_fc_b, "gelu_bias", precision)
    write_matrix_rows(f, f"{L}.mlp.down", c_proj_w, "linear", precision)
    write_vector(f, f"{L}.mlp.down.bias", c_proj_b, "linear_bias", precision)


def export_final(f, model, precision):
    """Final layer norm."""
    write_vector(f, "final.ln.weight", model.transformer.ln_f.weight.detach(), "layernorm", precision)
    write_vector(f, "final.ln.bias", model.transformer.ln_f.bias.detach(), "layernorm_bias", precision)


def main():
    parser = argparse.ArgumentParser(description="GPT-2 → text for Isaac")
    parser.add_argument("--output", "-o", default="gpt2_raw.txt", help="Output file path")
    parser.add_argument("--component", choices=["all", "embed", "attn", "mlp", "ln"],
                        default="all", help="Which components to export")
    parser.add_argument("--layer", type=int, default=None, help="Single layer (0-11)")
    parser.add_argument("--top-k-embed", type=int, default=None,
                        help="Only export top K token embeddings (by index)")
    parser.add_argument("--precision", type=int, default=4, help="Decimal places for weights")
    parser.add_argument("--model", default="gpt2", help="Model name (gpt2, gpt2-medium, etc.)")
    args = parser.parse_args()

    print(f"Loading {args.model}...")
    model = GPT2LMHeadModel.from_pretrained(args.model)
    tokenizer = GPT2Tokenizer.from_pretrained(args.model)
    model.eval()

    layers = [args.layer] if args.layer is not None else list(range(len(model.transformer.h)))

    line_count = 0
    with open(args.output, 'w') as f:
        # Embeddings
        if args.component in ("all", "embed"):
            print("Writing embeddings...")
            pos = f.tell()
            export_embeddings(f, model, tokenizer, args.precision, args.top_k_embed)
            lines = f.tell()  # approximate
            print(f"  embeddings done")

        # Transformer layers
        for layer_idx in layers:
            if args.component == "embed":
                continue

            print(f"Writing layer {layer_idx}...")

            if args.component in ("all", "attn"):
                block = model.transformer.h[layer_idx]
                L = f"layer{layer_idx}"
                # Attention components
                c_attn_w = block.attn.c_attn.weight.detach()
                c_attn_b = block.attn.c_attn.bias.detach()
                q_w, k_w, v_w = c_attn_w.split(768, dim=1)
                c_proj_w = block.attn.c_proj.weight.detach()
                c_proj_b = block.attn.c_proj.bias.detach()
                fmt = f"{{:.{args.precision}f}}"

                for head_idx in range(12):
                    h_s, h_e = head_idx * 64, (head_idx + 1) * 64
                    write_matrix_rows(f, f"{L}.attn.head{head_idx}.query",
                                     q_w[:, h_s:h_e], "query softmax", args.precision)
                    write_matrix_rows(f, f"{L}.attn.head{head_idx}.key",
                                     k_w[:, h_s:h_e], "key softmax", args.precision)
                    write_matrix_rows(f, f"{L}.attn.head{head_idx}.value",
                                     v_w[:, h_s:h_e], "value linear", args.precision)
                    write_matrix_rows(f, f"{L}.attn.head{head_idx}.output",
                                     c_proj_w[h_s:h_e, :], "attention_output linear", args.precision)

            if args.component in ("all", "mlp"):
                block = model.transformer.h[layer_idx]
                L = f"layer{layer_idx}"
                write_matrix_rows(f, f"{L}.mlp.up",
                                 block.mlp.c_fc.weight.detach(), "gelu", args.precision)
                write_matrix_rows(f, f"{L}.mlp.down",
                                 block.mlp.c_proj.weight.detach(), "linear", args.precision)

            if args.component in ("all", "ln"):
                block = model.transformer.h[layer_idx]
                L = f"layer{layer_idx}"
                write_vector(f, f"{L}.ln1.weight", block.ln_1.weight.detach(), "layernorm", args.precision)
                write_vector(f, f"{L}.ln1.bias", block.ln_1.bias.detach(), "layernorm_bias", args.precision)
                write_vector(f, f"{L}.ln2.weight", block.ln_2.weight.detach(), "layernorm", args.precision)
                write_vector(f, f"{L}.ln2.bias", block.ln_2.bias.detach(), "layernorm_bias", args.precision)

        # Final layer norm
        if args.component in ("all", "ln"):
            export_final(f, model, args.precision)

    # Count lines
    with open(args.output) as f:
        line_count = sum(1 for _ in f)

    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\nDone: {line_count:,} lines, {size_mb:.1f} MB → {args.output}")
    print(f"Feed through Isaac's front door.")


if __name__ == "__main__":
    main()
