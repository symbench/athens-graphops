# athens-graphops

* Clone it with `git clone git@github.com:symbench/athens-graphops.git --recurse-submodules`
* Install it with `pip3 install -e .`


# Using the StringerBuilder Class

The stringer builder class is meant to provide functionality to construct arbitrary design shapes in an automated manner. The designs are represented as strings generated from a design grammar in BNF. The generator code is located at: https://github.com/symbench/stringer.

Goals: provide a flexible routine for creating vehicles that adhere to a geometry encoded by design strings

Non-goals: optimal component and parameter selection for the design

The `StringerBuilder `class relies mainly on the `Designer` and `Architect` classes. However, there are 2 key differences which are meant to enable construction of arbitrary vehicle geometry:

1. Instruction generation: `StringerBuilder` includes a class method called `parse()` which will take a design string specified in the grammar format. The parse function then iterates over each token in the input design string to produce an instruction (i.e. a `Designer` function call e.g. `add_cylinder`)
2. Cursor for position awareness: complementary to the generated instructions is the `Cursor` class. This object is meant to provide locations for creating component connections and acts as the "glue" between subsequent instructions. The inspiration for this class comes mainly from the sequences of operations in the manually created hackathon 2 design submissions (VUdoo, etc.).