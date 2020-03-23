# Style attention alignments (Token weights) to be applied to GST when running tests.
# shape of alignments: [None, @heads, @token]
#   @heads: num of heads for style attention
#   @token: num of style tokens

_heads_num = 1
_token_num = 7
_min_weight = 1
_max_weight = 10
_weight_step = 1
test_alignments = []
for token in range(_token_num):
    test_alignments += [[[(0 if i != token else weight) for i in range(_token_num)] for _h in range(_heads_num)] for weight in range(_min_weight, _max_weight, _weight_step)]