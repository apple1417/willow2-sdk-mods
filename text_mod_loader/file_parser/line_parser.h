#ifndef FILE_PARSER_LINE_PARSER_H
#define FILE_PARSER_LINE_PARSER_H

#include "pch.h"
#include "parse_result.h"

namespace tml {

/**
 * @brief Parses through a generic file stream line by line.
 * @note Leaves the input stream on the first command.
 *
 * @param stream The stream to read from.
 * @param parse_result The parse result struct to extract comments into.
 */
void parse_file_line_by_line(std::istream& stream, ParseResult& parse_result);

}  // namespace tml

#endif /* FILE_PARSER_LINE_PARSER_H */
