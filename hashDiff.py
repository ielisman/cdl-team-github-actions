from deepdiff import DeepDiff

class HashComparator:
    def __init__(self):
        pass

    def initialize_nested_dict(self, dictionary, key, sub_key):
        if key not in dictionary:
            dictionary[key] = {}
        if sub_key not in dictionary[key]:
            dictionary[key][sub_key] = []

    def added_new_items(self, hash1, hash2):
        # find additions
        added_items = {}
        for key in hash2.keys():
            if key not in hash1:
                # look for subkeys and print them
                if isinstance(hash2[key], dict):
                    for sub_key in hash2[key].keys():                        
                        for item in hash2[key][sub_key]:
                            print(f"New location: {key} => {sub_key} => {item}")
                            self.initialize_nested_dict(added_items, key, sub_key)
                            added_items[key][sub_key] = item
            elif hash1[key] != hash2[key]:
                # check which subkeys are different
                for sub_key in hash2[key].keys():
                    if sub_key not in hash1[key]:                        
                        for item in hash2[key][sub_key]:
                            print(f"New date    : {key} => {sub_key} => {item}")
                            self.initialize_nested_dict(added_items, key, sub_key)
                            added_items[key][sub_key] = item
                    elif hash1[key][sub_key] != hash2[key][sub_key]:
                        # check what exactly is different
                        if isinstance(hash1[key][sub_key], list) and isinstance(hash2[key][sub_key], list):
                            for item in hash2[key][sub_key]:
                                if item not in hash1[key][sub_key]:
                                    print(f"New time    : {key} => {sub_key} => {item}")
                                    self.initialize_nested_dict(added_items, key, sub_key)
                                    added_items[key][sub_key] = item
        return added_items

    def compare_hashes(self, hash1, hash2, update_hash1=False):
        """
        Compare two hashes and optionally update the first hash with changes.

        :param hash1: The first hash (dictionary) to compare.
        :param hash2: The second hash (dictionary) to compare.
        :param update_hash1: If True, updates hash1 with changes from hash2.
        :return: A dictionary containing the differences.
        """
        # Compare the two hashes
        diff = DeepDiff(hash1, hash2, ignore_order=True)

        # Handle removed values
        if "dictionary_item_removed" in diff:
            removed_items = diff["dictionary_item_removed"]
            print("Removed items:")
            for key in removed_items:
                print(f"\t{key}")

        # Handle added values
        if "dictionary_item_added" in diff:
            added_items = diff["dictionary_item_added"]
            print("Added items:")
            for key in added_items:                
                if key.startswith("root['") and key.count("']") == 1:
                    top_level_key = key.split("['")[1].split("']")[0]
                    print(f"\tTop-level location added: {top_level_key}")
                    if top_level_key in hash2:
                        for sub_key in hash2[top_level_key]:
                            print(f"\t{key} => {sub_key} => {hash2[top_level_key][sub_key]}")

        # Handle changed values
        if "values_changed" in diff:
            changed_items = diff["values_changed"]
            print("Changed items:")
            for key, value in changed_items.items():
                print(f"\t{key}: {value}")

        # Handle sublist differences
        if "iterable_item_added" in diff:
            added_to_sublists = diff["iterable_item_added"]
            print("Items added to sublists:")
            for key, value in added_to_sublists.items():
                print(f"\t{key}: {value}")

        if "iterable_item_removed" in diff:
            removed_from_sublists = diff["iterable_item_removed"]
            print("Items removed from sublists:")
            for key, value in removed_from_sublists.items():
                print(f"\t{key}: {value}")

        return diff    

    @staticmethod
    def to_string(hash_data, indent=0):
        """
        Convert a hash (nested dictionary) to a readable string format.
        The deepest lists are printed on the same line as their keys.

        :param hash_data: The hash (dictionary) to convert.
        :param indent: The current indentation level (used for recursion).
        :return: A string representation of the hash.
        """
        result = ""
        for key, value in hash_data.items():
            result += " " * indent + f"{key}:"
            if isinstance(value, dict):
                result += "\n" + HashComparator.to_string(value, indent + 4)
            else:
                result += f" {value}\n"
        return result

# Example hashes
hash1 = {
    'location1': {
        '03/25/2005': ['8:30', '9:30'],
        '03/29/2005': ['8:30', '10:45']
    },
    'location2': {
        '03/30/2005': ['8:30','13:45'],
        '03/31/2005': ['9:30'],
        '04/10/2005': ['8:30']
    },
    'locationX': {        
    }
}

hash2 = {
    'location1': {
        '03/25/2005': ['8:30', '9:30'],
        '03/29/2005': ['8:30', '10:45', '12:45', '13:45']
    },
    'location2': {
        '03/29/2005': ['12:30'],
        '03/30/2005': ['8:30'],
        '03/31/2005': [],
    },
    'location3': {        
        '03/29/2005': ['8:30', '10:45', '12:45', '13:45']
    },    
}

# print("Hash1:\n", HashComparator.to_string(hash1))
# print("\nHash2:\n", HashComparator.to_string(hash2))
comparator = HashComparator()
added_items = comparator.added_new_items(hash1, hash2)
hash1 = hash2
# print("\nUpdated hash1:\n", HashComparator.to_string(hash1))