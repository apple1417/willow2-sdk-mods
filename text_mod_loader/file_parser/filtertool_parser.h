#ifndef FILE_PARSER_FILTERTOOL_PARSER_H
#define FILE_PARSER_FILTERTOOL_PARSER_H

#include "pch.h"
#include "parse_result.h"

namespace tml {

/**
 * @brief Parses through a filter tool file stream.
 * @note Leaves the input stream directly after the point where comments finish, on the first
 *       command or category header.
 *
 * @param stream The stream to read from.
 * @param parse_result The parse result struct to extract comments into.
 */
void parse_filtertool_file(std::istream& stream, ParseResult& parse_result);

}  // namespace tml

#endif /* FILE_PARSER_FILTERTOOL_PARSER_H */
