#
# Examples assumes that we have potentially more than one example, the goal
# is to create a block for examples.
#
from pybars import Compiler
import html


#
# We will use eos: </s> automatically in both train and decode. Prompt can decide whether
# and how they want to use bos: <s>.
# We need to have two path: one for training (we need extra_tokens) and one for decoding.
# In LUG, we call prompt needed by embedding instruction, as they are static. Templated prompt
# needed by generation will be called as prompt.
#
class ObjectLister:
    def __init__(
            self,
            item_header=None,
            item_header_delim: str = "\n",
            item_delim: str = "\n\n",
            block_header: str = "",
            block_tail: str = "",
            with_index: bool = True):
        self.item_header = item_header
        self.item_header_delim = item_header_delim
        self.item_delim = item_delim
        self.block_header = block_header
        self.block_tail = block_tail
        self.with_index = with_index

    def __call__(self, this, options, items):
        result = []
        # If the item list is empty.
        if len(items) == 0:
            return result
        result.append(self.block_header)
        for index, thing in enumerate(items):
            if self.item_header:
                if self.with_index:
                    result.append(f'{self.item_header} {index}) {self.item_header_delim}')
                else:
                    result.append(f'{self.item_header} {self.item_header_delim}')
            result.extend(options['fn'](thing))
            result.append(self.item_delim)
        result.append(self.block_tail)
        return result


#
# Assume the source have examples, slots, skills, values as well as utterance.
# This prompt template is designed to address template for full skill.
class Prompt:
    def __init__(self, source: str, extra_tokens=[]):
        self.template = Compiler().compile(source)
        self.extra_tokens = extra_tokens
        self.helpers = {
            'list_examples': ObjectLister(block_header="\nThe expression templates are:\n", item_header="Expression template"),
            'list_skills': ObjectLister(block_header="\nGiven the functions and their descriptions:\n", item_delim="\n"),
            'list_skill_names': ObjectLister(item_header=None, item_delim=",", block_header="[", block_tail="]"),
            'list_slots': ObjectLister(item_header=None, item_delim=",", block_header="[", block_tail="]"),
            'list_values': ObjectLister(item_header=None, item_delim=",", block_header="[", block_tail="]"),
        }
        self.partials = {}

    def __call__(self, item: dict[str, any]) -> str:
        # First we need to create the example.
        return html.unescape(self.template(item, helpers=self.helpers, partials=self.partials))


#
# LugPrompts assumes the following prompt template in pybars depending on the following information:
# skills: List[SkillSpec]
# slots: List[SlotSpec]
# exemplars: List[Exemplar]
# values: ?
#

SkillPrompts = {
    "specs_only":
        Prompt(
            "{{#list_skills skills}} [ {{name}} ] : {{description}} {{/list_skills}}\n"
            "Classify the input sentence as one of {{#list_skill_names skills}} {{name}} {{/list_skill_names}}.\n"
            "### Input sentence: {{utterance}}\n"
            "### Output:"),
    "specs_exampled":
        Prompt(
            "{{#list_skills skills}} [ {{name}} ] : {{description}} {{/list_skills}}\n"
            "{{#list_examples examples}}### Input template: {{template}}\n### Output:[ {{owner}} ]\n{{/list_examples}}\n"
            "Classify the input sentence as one of {{#list_skill_names skills}} {{name}} {{/list_skill_names}}.\n"
            "### Input sentence: {{utterance}}\n"
            "### Output:"),
}

# For the slots of enum type, we used different prompt in order to improve the
SlotPrompts = {
    "default":
        Prompt(
            "{{#list_values values}} value {{/list_values}}\n"
            "Extract the value for parameter {{name}} ({{description}}) from and only from the given input:\n"
            "### Input: {{utterance}}\n"
            "### Output:"),
    "basic":
        Prompt(
            "Extract the value for parameter {{name}} ({{description}}) from and only from the given input:\n"
            "### Input: {{utterance}}\n"
            "### Output:"),
}
