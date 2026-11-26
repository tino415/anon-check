from conftest import NameListModel

from anon_check.detect import CHUNK_CHARS, Cell, find_in_cells, find_in_text, split_into_chunks


def test_chunks_cover_the_whole_text_without_whitespace():
    text = "x" * 2000
    chunks = split_into_chunks(text)
    assert chunks[0][0] == 0
    assert chunks[-1][0] + len(chunks[-1][1]) == len(text)
    assert all(len(chunk) <= CHUNK_CHARS for _, chunk in chunks)


def test_a_name_cut_by_a_chunk_boundary_is_found_whole():
    text = "a " * 396 + "x Ján Novák" + " b" * 300
    first_chunk = split_into_chunks(text)[0][1]
    assert first_chunk.endswith("Ján ")
    assert [(s.start, s.length, s.type) for s in find_in_text(text, NameListModel("Ján Novák"))] == [(794, 9, "PERSON")]


def test_a_long_cell_reaches_the_model_in_chunks_with_its_header():
    cell = "a " * 1000 + "Ján Novák"
    model = NameListModel("Ján Novák")
    [spans] = find_in_cells([Cell(cell, "Poznámka")], model)
    assert [(s.start, s.length) for s in spans] == [(2000, 9)]
    assert len(model.inputs) > 1
    assert all(text.startswith("Poznámka: ") for text in model.inputs)
