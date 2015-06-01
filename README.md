# Parse.py                    
Process text like never before.

## Info
Parse.py is Python module that will let you process strings and generate structured output.

## Usage
### Documentation
#### Objects
* `word(chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")` - Will match a word that contains these characters.
* `liter(lit)` - Will match a piece of input that exactly match argument, doesn't require whitespaces around.
* `key(k)` - Will match a piece of input that exactly match argument, require whitespaces around.
* `And(first, second)` - Will match two elements one-after-another.
* `Or(first, second)` - Will match one or two elements one-after-another.
* `Xor(first, second)` - Will match the longest element.
* `$1 + $2` - Will create `And($1, $2)` object.
* `$1 | $2` - Will create `Or($1, $2)` object.
* `$1 ^ $2` - Will create `Xor($1, $2)` object.
* `optional(value)` - Will match the given sequence if can, else it not.
* `group(value)` - Will match the given sequence and round it to tuple.
* `count(cnt)` - Will create callable count object.
* `count.more(value)` - Will match the given count and more of elements.
* `count.less(value)` - Will match count from one to the given count of elements.
* `count.upTo(max, value)` - Will match count between the given count and the `max`imal count of given elements.
* `name(nam, value)` - Will match the `value` as value in `dict` and the `nam` as the key.
* `recurse()` - Will add object ID to database, then add code registered with ID and then run the code using its ID.
* `$1 << $2` - Will add value to `recurse` object.

Plus upcoming objects:
* `combine(value)` - Will `"".join(...)` the output of its `value`.

#### Functions and constants
* `setIgnored(val)` - Set ignored characters.
