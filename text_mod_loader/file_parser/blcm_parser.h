#ifndef FILE_PARSER_BLCM_PARSER_H
#define FILE_PARSER_BLCM_PARSER_H

#include "pch.h"
#include "parse_result.h"

namespace tml {

/**
 * @brief Parses through a blcmm file stream.
 * @note Leaves the stream directly after the line with the closing `</BLCMM>` tag.
 *
 * @param stream The stream to read from.
 * @param parse_result The parse result struct to extract comments and the recommended game into.
 */
void parse_blcmm_file(std::istream& stream, ParseResult& parse_result);

}  // namespace tml

#endif /* FILE_PARSER_BLCM_PARSER_H */
