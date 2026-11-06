"""Slide 6.5: put the answer into the context.

The aligned model gets a list of Physics Nobel winners per year, then the question for one year.
For each year we check whether the first name it predicts is right, and which list line the
heads attend to while it predicts that name.

Run from the repo root: .venv/bin/python demos/context_list.py [first_year last_year]
"""
import sys

sys.path.insert(0, ".")
import torch
from llm_helpers import ALIGNED, chat, chat_prompt, encode, load

WINNERS = {
    1915: "William Henry Bragg and William Lawrence Bragg", 1916: "not awarded", 1917: "Charles Glover Barkla",
    1918: "Max Planck", 1919: "Johannes Stark", 1920: "Charles Édouard Guillaume", 1921: "Albert Einstein",
    1922: "Niels Bohr", 1923: "Robert Millikan", 1924: "Manne Siegbahn", 1925: "James Franck and Gustav Hertz",
    1926: "Jean Perrin", 1927: "Arthur Compton and Charles Thomson Rees Wilson", 1928: "Owen Richardson",
    1929: "Louis de Broglie", 1930: "Chandrasekhara Venkata Raman", 1931: "not awarded", 1932: "Werner Heisenberg",
    1933: "Erwin Schrödinger and Paul Dirac", 1934: "not awarded", 1935: "James Chadwick",
    1936: "Victor Franz Hess and Carl David Anderson", 1937: "Clinton Davisson and George Paget Thomson",
    1938: "Enrico Fermi", 1939: "Ernest Lawrence", 1940: "not awarded", 1941: "not awarded", 1942: "not awarded",
    1943: "Otto Stern", 1944: "Isidor Isaac Rabi", 1945: "Wolfgang Pauli", 1946: "Percy Williams Bridgman",
    1947: "Edward Victor Appleton", 1948: "Patrick Blackett", 1949: "Hideki Yukawa", 1950: "Cecil Frank Powell",
    1951: "John Cockcroft and Ernest Walton", 1952: "Felix Bloch and Edward Mills Purcell", 1953: "Frits Zernike",
    1954: "Max Born and Walther Bothe", 1955: "Willis Lamb and Polykarp Kusch",
    1956: "William Shockley, John Bardeen and Walter Brattain", 1957: "Chen Ning Yang and Tsung-Dao Lee",
    1958: "Pavel Cherenkov, Ilya Frank and Igor Tamm", 1959: "Emilio Segrè and Owen Chamberlain",
    1960: "Donald Arthur Glaser",
}


def question(year):
    return f"Who won the Nobel Prize in Physics in {year}? Answer in one sentence."


def prompt(model, year, winners):
    """The chat document, ending where the model has to write the first name."""
    lines = "\n".join(f"{y}: {w}" for y, w in winners.items())
    user = f"Nobel Prize winners in Physics:\n{lines}\n\n{question(year)}"
    return chat_prompt(model.tok, user) + f"The Nobel Prize in Physics in {year} was awarded to", lines


@torch.no_grad()
def check(model, year, winners):
    text, lines = prompt(model, year, winners)
    out = model(encode(model, text), output_attentions=True)
    att = torch.stack(out.attentions)[:, 0, :, -1].float().cpu()  # layer, head, key: attention from the last position
    p = out.logits[0, -1].float().softmax(-1)
    first = model.tok.decode(p.argmax().item())
    right = winners[year].split()[0]  # the first word of the line we put in
    # token span of each list line, from character offsets
    offsets = model.tok(text, return_offsets_mapping=True, add_special_tokens=False).offset_mapping
    start = text.index(lines)
    spans, pos = {}, start
    for y, line in zip(winners, lines.split("\n")):
        spans[y] = [i for i, (a, b) in enumerate(offsets) if a < pos + len(line) and b > pos]
        pos += len(line) + 1
    mass = {y: att[:, :, s].sum(-1) for y, s in spans.items()}  # layer, head
    best = max(((mass[year][l, h].item(), l, h) for l in range(att.shape[0]) for h in range(att.shape[1])))
    _, l, h = best
    rivals = sorted(((mass[y][l, h].item(), y) for y in winners if y != year), reverse=True)[0]
    return first, right, p.max().item(), (l, h, best[0]), rivals


if __name__ == "__main__":
    lo, hi = (int(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (1945, 1960)
    winners = {y: w for y, w in WINNERS.items() if lo <= y <= hi}
    model = load(ALIGNED)
    n_tokens = encode(model, prompt(model, lo, winners)[0]).shape[1]
    print(f"List {lo}–{hi}: {len(winners)} lines, {n_tokens} tokens in the prompt\n")
    hits = 0
    for year in winners:
        if winners[year] == "not awarded":
            continue
        first, right, p, (l, h, m), (m2, y2) = check(model, year, winners)
        ok = right.startswith(first.strip())  # the first token may be only part of the name, e.g. ' F' for Frits
        hits += ok
        print(f"{year}: {first!r:14} {p:4.0%}  {'ok ' if ok else 'NO '} (want {right!r})  "
              f"head {l}.{h}: {m:.0%} on the {year} line, next best {y2} line {m2:.0%}")
    print(f"\n{hits} right first tokens")
    if 1951 in winners:
        lines = "\n".join(f"{y}: {w}" for y, w in winners.items())
        print("\nGreedy answer for 1951:", chat(model, f"Nobel Prize winners in Physics:\n{lines}\n\n{question(1951)}", max_new_tokens=40))
