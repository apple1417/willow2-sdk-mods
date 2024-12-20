#ifndef FILE_PARSER_BLCM_PARSER_H
#define FILE_PARSER_BLCM_PARSER_H

#include "pch.h"

namespace tml {

/**
 * @brief Parses through a blcmm file stream.
 * @note Leaves the stream directly after the line with the closing `</BLCMM>` tag.
 *
 * @return A list of description comments, and the detected recommended game.
 */
std::pair<std::vector<py::str>, std::optional<py::str>> parse_blcmm_file(std::istream& stream);

}  // namespace tml

#endif /* FILE_PARSER_BLCM_PARSER_H */
