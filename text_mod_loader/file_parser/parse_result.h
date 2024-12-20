#ifndef FILE_PARSER_PARSE_RESULT_H
#define FILE_PARSER_PARSE_RESULT_H

#include "pch.h"

namespace tml {

struct ParseResult {
    // Unordered map doesn't like working with python strings, have to store tags as a python dict
    py::dict blimp_tags;
    std::vector<py::str> untagged_lines;
    std::optional<py::str> game;
    std::optional<size_t> spark_service_idx;

    /**
     * @brief Discards all previously added comments.
     */
    void discard_comments(void);

    /**
     * @brief Adds a description comment to the relevant field.
     *
     * @param comment The comment to add.
     */
    void add_comment(const char* comment);
    void add_comment(const std::string& comment);
};

}  // namespace tml

#endif /* FILE_PARSER_PARSE_RESULT_H */
