from pyzhuyin import pinyin_to_zhuyin


class ChineseSymbol:
    """
    Class for Chinese symbols
    """
    traditional_symbol: str = ""
    simplified_symbol: str = ""
    pinyin: str = ""
    english_translation: list[str] = []
    zhuyin: str = ""

    def __init__(self,
                 traditional_symbol: str,
                 simplified_symbol: str,
                 pinyin: str,
                 english_translation: list[str],
                 ):
        self.traditional_symbol: str = traditional_symbol
        self.simplified_symbol: str = simplified_symbol
        self.pinyin: str = pinyin
        self.english_translation: list[str] = english_translation

        self._get_zhuyin()

    def __str__(self):
        return f"""
    traditional_symbol: {self.traditional_symbol}
    simplified_symbol: {self.simplified_symbol}
    pinyin: {self.pinyin}
    english_translation: {self.english_translation}
    zhuyin: {self.zhuyin}
            """

    def _get_zhuyin(self) -> None:
        """
        get the zhuyin representation of pinyin
        :return:
        """
        try:

            zhuyin: str = pinyin_to_zhuyin(self.pinyin)
            self.zhuyin = zhuyin
        except Exception as e:
            pass


def read_file_to_list(source: str) -> list[str]:
    """
    open the source file and cleans out the lines comment
    :param source:
    :return: list of lines
    """
    clean_lines: list[str] = []
    with open(source, 'r') as source_file:
        lines = source_file.readlines()
        for line in lines:
            if line.startswith('#'):
                continue

            clean_lines.append(line)

    return clean_lines


def create_objects_from_src(src_lines: list[str],
                            complete: bool = True
                            ) -> list[ChineseSymbol]:
    """
    creates objects for given lines from cedit_ts.u8
    :param src_lines: list with all lines from source file
    :param complete: if false, all items with more than one character in the traditional symbol are excluded
    :return: list of objects for chinese Symbol
    """
    objects: list = []
    for line in src_lines:
        items: list[str] = line.split(" ")

        if not complete:
            if len(items[0]) > 1:
                continue

        traditional_symbol: str = items[0]
        simplified_symbol: str = items[1]
        pinyin: str = items[2].replace("[", "").replace("]", "")

        english_translation: list[str] = items[3].split("/")
        english_translation_clean: list[str] = []
        for item in english_translation:
            if item == '':
                continue
            english_translation_clean.append(item)

        symbol_object = ChineseSymbol(traditional_symbol,
                                      simplified_symbol,
                                      pinyin,
                                      english_translation_clean,
                                      )

        objects.append(symbol_object)

    return objects


def create_lookup_table_lines(symbols: list[ChineseSymbol],
                              zhuyin_seperated: bool = False,
                              space_end: bool = False
                              ) -> list[str]:
    """
    creates the lines for the look-up table
    :param symbols: list with symbol classes
    :param zhuyin_seperated: if true, it creates a line with each zhuyin character e.g.:
                AddToTable("ㄙ", "㒸");
                AddToTable("ㄙㄨ", "㒸");
                AddToTable("ㄙㄨㄟ", "㒸");
    :param space_end: if true, at the end of zhuyin representation a space is added
    :return: list with lines for cpp-file
    """
    lines: list[str] = []
    for symbol in symbols:

        if symbol.zhuyin == "":
            continue

        if zhuyin_seperated:
            zhuyin_symbols = [symbol for symbol in symbol.zhuyin]

            for i in range(1, len(zhuyin_symbols) + 1):
                combined_symbols = "".join(zhuyin_symbols[:i])
                line = f'AddToTable("{combined_symbols}", "{symbol.traditional_symbol}");'
                lines.append(line)
                continue


        if space_end:
            line = f'AddToTable("{symbol.zhuyin} ", "{symbol.traditional_symbol}");'
            lines.append(line)
            continue

        line = f'AddToTable("{symbol.zhuyin}", "{symbol.traditional_symbol}");'
        lines.append(line)

    return lines

def split_list(list: list[any], splitting_size: int) -> list[list[any]]:
    """
    split a given list to many lists with given size
    :param list: list to split
    :param splitting_size:  the size to split
    :return: list with split lists
    """
    return [list[i:i + splitting_size] for i in range(0, len(list), splitting_size)]


def create_ccp_file(pobomofo_lines: list[str], filename: str):
    """
    creates the cpp look-up file
    :param pobomofo_lines: list with formatted lines
    :param filename: name of outputfile
    :return:
    """
    split_bopomofo_lines = split_list(list=pobomofo_lines,
                                      splitting_size=99
                                      )

    cpp_functions: list[str] = []
    call_lookuptabe: list[str] = []
    counter = 0
    for item in split_bopomofo_lines:
        cpp_function: str = f"void TBoPoMoFoTraditionalChineseLookupTable::LoadLookupTable{counter}() " + "{ \n"

        item_string = " \n".join(item)
        cpp_function = cpp_function + item_string
        cpp_function = cpp_function + "\n} \n \n"

        cpp_functions.append(cpp_function)

        call_lookuptabe.append(f"LoadLookupTable{counter}();")

        counter += 1

    output: str = '#include "BoPoMoFoTraditionalChinese.h"\n\n'
    output: str = output + "".join(cpp_functions)

    call_function: str = """void TBoPoMoFoTraditionalChineseLookupTable::LoadLookupTable() { \n
    if (InitTable == true)
	    return;
	"""

    call_function = call_function + "\n".join(call_lookuptabe)

    output = output + call_function

    output = output + "\n\nInitTable = true; \n}"

    with open(filename + ".cpp", "w") as file:
        file.write(output)


if __name__ == '__main__':
    source_lines = read_file_to_list('src/cedict_1_0_ts_utf-8_mdbg.txt')

    """
    complete list of symbols with phrases
    """
    # symbol_objects: list[ChineseSymbol] = create_objects_from_src(src_lines=source_lines,
    #                                                                    complete=True
    #                                                                    )

    """
    list of symbols with one character (just words)    
    """
    symbol_objects: list[ChineseSymbol] = create_objects_from_src(src_lines=source_lines,
                                                                  complete=False
                                                                  )


    pobomofo_lines = create_lookup_table_lines(symbols=symbol_objects,
                                               zhuyin_seperated=False,
                                               space_end=True
                                               )
    create_ccp_file(pobomofo_lines, "pobomofo_file")
