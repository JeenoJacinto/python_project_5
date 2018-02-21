import string

def slugify_title(title):
    """Filters out and replaces unsafe url characters"""
    safe_character_list = (
        list(string.ascii_lowercase)
        + list(string.ascii_uppercase)
        + ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-']
    )
    replaced_spaces = title.replace(" ", "-")
    word_list = []
    fmt_word_list = []
    for character in replaced_spaces:
        word_list.append(character)
    for character in word_list:
        if character in safe_character_list:
            fmt_word_list.append(character)
    fmt_word_list = "".join(fmt_word_list)
    return fmt_word_list
