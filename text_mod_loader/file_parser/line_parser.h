#ifndef FILE_PARSER_LINE_PARSER_H
#define FILE_PARSER_LINE_PARSER_H

#include "pch.h"

namespace tml {

/**
 * @brief Parses through a generic file stream line by line.
 * @note Leaves the input stream on the first command.
 *
 * @return A list of description comments.
 */
std::vector<py::str> parse_file_line_by_line(std::istream& stream);

}  // namespace tml

#endif /* FILE_PARSER_LINE_PARSER_H */
