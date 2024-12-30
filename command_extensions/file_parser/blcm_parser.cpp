#include "pch.h"
#include "blcm_parser.h"
#include "blcm_preprocessor/blcm_preprocessor.h"
#include "matcher.h"

namespace ce {

namespace {

// Holds info about a "block" of consecutive commands, within the same category.
// `CE_EnableOn` commands split blocks, but the same object can be reused between them.
struct CommandBlock {
    // This is slightly bad practice, but we're not using this as a normal class, we'll never
    // transfer these objects, it makes the code cleaner to just act like they're all locals
    // NOLINTNEXTLINE(cppcoreguidelines-avoid-const-or-ref-data-members)
    std::vector<CommandMatch>& output;

    std::vector<CommandMatch> cached_commands;
    EnableStrategy strategy;
    bool any_enabled = false;
    bool any_disabled = false;

    CommandBlock(std::vector<CommandMatch>& output, EnableStrategy strategy)
        : output(output), strategy(strategy) {}
    ~CommandBlock() { this->handle_block_end(); }

    CommandBlock(const CommandBlock&) = delete;
    CommandBlock(CommandBlock&&) noexcept = delete;
    CommandBlock& operator=(const CommandBlock&) = delete;
    CommandBlock& operator=(CommandBlock&&) noexcept = delete;

   private:
    /**
     * @brief Handles reaching the end of the block.
     */
    void handle_block_end() {
        switch (this->strategy) {
            case EnableStrategy::ALL:
                if (!this->any_disabled) {
                    this->output.insert(output.end(), this->cached_commands.begin(),
                                        this->cached_commands.end());
                }
                break;
            case EnableStrategy::ANY:
                if (this->any_enabled) {
                    this->output.insert(output.end(), this->cached_commands.begin(),
                                        this->cached_commands.end());
                }
                break;

            case EnableStrategy::FORCE:
            case EnableStrategy::NEXT:
                break;
        }

        this->cached_commands.clear();
        this->any_enabled = false;
        this->any_disabled = false;
    }

    /**
     * @brief Updates the current enable strategy.
     *
     * @param val The strategy to swap to.
     */
    void update_enable_strategy(CaseInsensitiveStringView val) {
        auto non_space = std::ranges::find_if_not(val, [](auto chr) { return std::isspace(chr); });
        if (non_space == val.end()) {
            return;
        }
        auto strategy_end =
            std::find_if(non_space, val.end(), [](auto chr) { return std::isspace(chr); });

        auto strategy_name = CaseInsensitiveStringView{non_space, strategy_end};

        static const constexpr CaseInsensitiveStringView strategy_all = "All";
        static const constexpr CaseInsensitiveStringView strategy_any = "Any";
        static const constexpr CaseInsensitiveStringView strategy_force = "Force";
        static const constexpr CaseInsensitiveStringView strategy_next = "Next";

        EnableStrategy new_strategy{};
        if (strategy_name == strategy_all) {
            new_strategy = EnableStrategy::ALL;
        } else if (strategy_name == strategy_any) {
            new_strategy = EnableStrategy::ANY;
        } else if (strategy_name == strategy_force) {
            new_strategy = EnableStrategy::FORCE;
        } else if (strategy_name == strategy_next) {
            new_strategy = EnableStrategy::NEXT;
        } else {
            return;
        }

        this->handle_block_end();

        this->strategy = new_strategy;
    }

   public:
    /**
     * @brief Handles encountering a standard command.
     *
     * @param is_enabled True if the command is enabled.
     */
    void handle_standard_command(bool is_enabled) {
        if (is_enabled) {
            this->any_enabled = true;
        } else {
            this->any_disabled = true;
        }

        switch (this->strategy) {
            case EnableStrategy::ALL:
            case EnableStrategy::ANY:
            case EnableStrategy::FORCE:
                break;

            case EnableStrategy::NEXT:
                if (is_enabled) {
                    output.insert(output.end(), this->cached_commands.begin(),
                                  this->cached_commands.end());
                }
                this->cached_commands.clear();
                break;
        }
    }

    /**
     * @brief Handles encountering a custom command.
     *
     * @param cmd The command which was matched.
     * @param line The full line which was matched.
     * @param match The match object.
     */
    void handle_standard_command(std::string_view cmd,
                                 std::string_view line,
                                 CommandMatch&& match) {
        static const constexpr CaseInsensitiveStringView enable_on = "CE_EnableOn";
        if (cmd == enable_on) {
            this->update_enable_strategy(line.substr(match.cmd_len));
            return;
        }
        static const constexpr CaseInsensitiveStringView new_cmd = "CE_NewCmd";
        if (cmd == new_cmd) {
            add_new_command(line.substr(match.cmd_len));
            return;
        }

        switch (this->strategy) {
            case EnableStrategy::ALL:
            case EnableStrategy::ANY:
            case EnableStrategy::NEXT:
                this->cached_commands.emplace_back(std::move(match));
                break;

            case EnableStrategy::FORCE:
                this->output.emplace_back(std::move(match));
                break;
        }
    }
};

/**
 * @brief Recursively look through BLCMM categories and extract all enabled commands within them.
 *
 * @param category The XML category to look through.
 * @param input_strategy The current enable strategy.
 * @param output The list of commands to output to.
 * @param profile The file's selected profile.
 * @param cmd_names The set of valid command names.
 */
void handle_category(const pugi::xml_node& category,
                     EnableStrategy input_strategy,
                     std::vector<CommandMatch>& output,
                     std::string_view profile) {
    CommandBlock block{output, input_strategy};

    auto handle_child_element = [&](std::string_view child_name, const pugi::xml_node& child) {
        static const constexpr CaseInsensitiveStringView category = "category";
        if (child_name == category) {
            handle_category(child, block.strategy, output, profile);
            return;
        }

        static const constexpr CaseInsensitiveStringView comment = "comment";
        if (child_name == comment) {
            const std::string_view line = child.child_value();
            auto [cmd, match] = try_match_command(line);
            if (!cmd.empty()) {
                block.handle_standard_command(cmd, line, std::move(match));
            }
            return;
        }

        static const constexpr CaseInsensitiveStringView code = "code";
        if (child_name == code) {
            auto is_enabled = blcm_preprocessor::in_comma_separated_list(
                profile, child.attribute("profiles").as_string());

            block.handle_standard_command(is_enabled);
            return;
        }
    };

    // Main pass through
    for (auto child : category) {
        const std::string_view child_name = child.name();

        // If the child element is a hotfix, all of it's children are on this layer logically
        static const constexpr CaseInsensitiveStringView hotfix = "hotfix";
        if (child.name() == hotfix) {
            for (auto hotfix_child : child) {
                handle_child_element(hotfix_child.name(), hotfix_child);
            }
            continue;
        }

        handle_child_element(child_name, child);
    }
}

}  // namespace

std::vector<CommandMatch> parse_blcmm_file(std::istream& stream) {
    std::stringstream processed_xml{};
    blcm_preprocessor::preprocess(stream, processed_xml);
    // Move the string out of the stream
    auto processed_str = std::move(processed_xml).str();

    pugi::xml_document doc{};
    // Use latin1 to try avoid any char conversions
    auto res = doc.load_buffer_inplace(processed_str.data(), processed_str.size(),
                                       pugi::parse_default, pugi::encoding_latin1);
    if (res.status != pugi::status_ok) {
        throw blcm_preprocessor::ParserError(res.description());
    }

    auto profile = doc.select_node("/BLCMM/head/profiles/profile[@name][@current='true']/@name")
                       .attribute()
                       .as_string("default");

    auto root = doc.select_node("/BLCMM/body/category").node();
    if (root == nullptr) {
        throw blcm_preprocessor::ParserError("Couldn't find root category");
    }

    std::vector<CommandMatch> output{};
    handle_category(root, EnableStrategy::ANY, output, profile);

    return output;
}

}  // namespace ce
