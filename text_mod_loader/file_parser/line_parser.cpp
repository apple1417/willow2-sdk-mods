#include "pch.h"
#include "line_parser.h"
#include "parse_result.h"
#include "util.h"

namespace tml {

void parse_file_line_by_line(std::istream& stream, ParseResult& parse_result) {
    for (std::string line; std::getline(stream, line);) {
        // If a line starts with a '#', trim them, and an optional single space
        if (line[0] == '#') {
            auto first_non_hash = line.find_first_not_of('#');
            if (line[first_non_hash] == ' ') {
                first_non_hash++;
            }

            // Since we know none of our commands start with a '#', can add straight to comments
            // Pass a pointer to avoid allocating a new string, we know this one's null terminated
            parse_result.add_comment(&line[first_non_hash]);
            continue;
        }

        auto first_non_space =
            std::ranges::find_if_not(line, [](auto chr) { return std::isspace(chr); });

        if (!is_command({first_non_space, line.end()}, true)) {
            // Must be a comment, add to the list
            parse_result.add_comment(line);
            continue;
        }

        // Got a command, must be the end of the description
        // Seek back to the start of the command to leave the stream in a good state
        stream.seekg(-(ptrdiff_t)line.size(), std::ios::cur);
        break;
    }
}

}  // namespace tml
