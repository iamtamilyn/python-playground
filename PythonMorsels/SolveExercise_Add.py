from copy import deepcopy
import unittest


def add(*lists):
    for x in args:
        raise ValueError("not same length")
    #test len of sub lists

    final_list = []
    for x in range(len(list_one)):
        final_list.append([list_one[x][i] + list_two[x][i] for i in range(len(list_one[x]))])
        #print(final_list)

    return final_list

m1 = [[6, 6], [3, 1]]
m2 = [[1, 2], [3, 4]]
result = add(m1, m2)
print(result)

#zip...


class AddTests(unittest.TestCase):

    """Tests for add."""

    def test_single_items(self):
        self.assertEqual(add([[5]], [[-2]]), [[3]])

    def test_two_by_two_matrixes(self): 
        m1 = [[6, 6], [3, 1]]
        m2 = [[1, 2], [3, 4]]
        m3 = [[7, 8], [6, 5]]
        self.assertEqual(add(m1, m2), m3)

    def test_two_by_three_matrixes(self): 
        m1 = [[1, 2, 3], [4, 5, 6]]
        m2 = [[-1, -2, -3], [-4, -5, -6]]
        m3 = [[0, 0, 0], [0, 0, 0]]
        self.assertEqual(add(m1, m2), m3)

    def test_input_unchanged(self): 
        m1 = [[6, 6], [3, 1]]
        m2 = [[1, 2], [3, 4]]
        m1_original = deepcopy(m1)
        m2_original = deepcopy(m2)
        add(m1, m2)
        self.assertEqual(m1, m1_original)
        self.assertEqual(m2, m2_original)

unittest.main(verbosity=2)