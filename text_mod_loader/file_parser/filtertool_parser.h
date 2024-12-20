#ifndef FILE_PARSER_FILTERTOOL_PARSER_H
#define FILE_PARSER_FILTERTOOL_PARSER_H

#include "pch.h"

namespace tml {

/**
 * @brief Parses through a filter tool file stream.
 * @note Leaves the input stream directly after the point where comments finish, on the first
 *       command or category header.
 *
 * @return A list of description comments.
 */
std::vector<py::str> parse_filtertool_file(std::istream& stream);

}  // namespace tml

#endif /* FILE_PARSER_FILTERTOOL_PARSER_H */
