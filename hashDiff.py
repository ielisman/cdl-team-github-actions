class HashComparator:
    def __init__(self):
        pass

    def initialize_nested_dict(self, dictionary, location, appointment_date):
        if location not in dictionary:
            dictionary[location] = {}
        if appointment_date not in dictionary[location]:
            dictionary[location][appointment_date] = []

    def diff(self, hash1, hash2, printAnalysis=False):
    
        same_times = {}
        added_locations = {}
        added_dates = {}
        added_times = {}
        removed_locations = {}
        removed_dates = {}
        removed_times = {}

        for location in hash2.keys():
            if location not in hash1:                
                if isinstance(hash2[location], dict):
                    for appointment_date in hash2[location].keys():                        
                        for times_slot in hash2[location][appointment_date]:
                            if printAnalysis:
                                print(f"New location: {location} => {appointment_date} => {times_slot}")
                            self.initialize_nested_dict(added_locations, location, appointment_date)
                            added_locations[location][appointment_date].append(times_slot)
            elif hash1[location] != hash2[location]:                
                for appointment_date in hash2[location].keys():
                    if appointment_date not in hash1[location]:                       
                        for times_slot in hash2[location][appointment_date]:
                            if printAnalysis:
                                print(f"New date    : {location} => {appointment_date} => {times_slot}")
                            self.initialize_nested_dict(added_dates, location, appointment_date)
                            added_dates[location][appointment_date].append(times_slot)
                    elif hash1[location][appointment_date] != hash2[location][appointment_date]:
                        # check what exactly is different
                        if isinstance(hash1[location][appointment_date], list) and isinstance(hash2[location][appointment_date], list):
                            for times_slot in hash2[location][appointment_date]:
                                if times_slot not in hash1[location][appointment_date]:
                                    if printAnalysis:
                                        print(f"New time    : {location} => {appointment_date} => {times_slot}")
                                    self.initialize_nested_dict(added_times, location, appointment_date)
                                    added_times[location][appointment_date].append(times_slot)
                    elif hash1[location][appointment_date] == hash2[location][appointment_date]:
                        if printAnalysis:
                            print(f"Same {location} {appointment_date} for hash1 and hash2: {hash2[location][appointment_date]}")
                        self.initialize_nested_dict(same_times, location, appointment_date)
                        same_times[location][appointment_date] = hash2[location][appointment_date]

        for location in hash1.keys():
            if location not in hash2:
                if printAnalysis:
                    print(f"removed location {location}: {hash1[location]}")
                removed_locations[location] = hash1[location]
            else:
                if isinstance(hash1[location], dict):
                    for appointment_date in hash1[location].keys():
                        if appointment_date not in hash2[location]:
                            if printAnalysis:
                                print(f"removed date    : {location} => {appointment_date} => {hash1[location][appointment_date]}")
                            self.initialize_nested_dict(removed_dates, location, appointment_date)
                            removed_dates[location][appointment_date] = hash1[location][appointment_date]
                        else:
                             if isinstance(hash1[location][appointment_date], list) and isinstance(hash2[location][appointment_date], list):
                                for times_slot in hash1[location][appointment_date]:
                                    if times_slot not in hash2[location][appointment_date]:
                                        if printAnalysis:
                                            print(f"Removed time    : {location} => {appointment_date} => {times_slot}")
                                        self.initialize_nested_dict(removed_times, location, appointment_date)
                                        removed_times[location][appointment_date].append(times_slot)

        return  { 'same_times': same_times, 
                  'added_locations': added_locations, 'added_dates': added_dates, 'added_times': added_times, 
                  'removed_locations': removed_locations, 'removed_dates': removed_dates, 'removed_times': removed_times
                }   

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

# # Example hashes
# hash1 = {
#     'location1': {
#         '03/25/2005': ['8:30', '9:30'],
#         '03/29/2005': ['8:30', '10:45']
#     },
#     'location2': {
#         '03/30/2005': ['8:30','13:45'],
#         '03/31/2005': ['9:30'],
#         '04/10/2005': ['8:30']
#     },
#     'locationX': {
#         '03/31/2005': ['9:30']     
#     }
# }

# hash2 = {
#     'location1': {
#         '03/25/2005': ['8:30', '9:30'],
#         '03/29/2005': ['10:45', '12:45', '13:45'] # '03/29/2005': ['8:30', '10:45', '12:45', '13:45']
#     },
#     'location2': {
#         '03/29/2005': ['12:30'],
#         '03/30/2005': ['8:30'],
#         '03/31/2005': [],
#     },
#     'location3': {        
#         '03/29/2005': ['8:30', '10:45', '12:45', '13:45']
#     },    
# }

# comparator = HashComparator()
# added_items = comparator.diff(hash1, hash2, printAnalysis=False)
# print("\n")
# print(HashComparator.to_string(added_items))
# hash1 = hash2
# print("\nUpdated hash1:\n", HashComparator.to_string(hash1))

# from deepdiff import DeepDiff
#
# def compare_hashes(self, hash1, hash2, update_hash1=False):
#     """
#     Compare two hashes and optionally update the first hash with changes.

#     :param hash1: The first hash (dictionary) to compare.
#     :param hash2: The second hash (dictionary) to compare.
#     :param update_hash1: If True, updates hash1 with changes from hash2.
#     :return: A dictionary containing the differences.
#     """
#     # Compare the two hashes
#     diff = DeepDiff(hash1, hash2, ignore_order=True)

#     # Handle removed values
#     if "dictionary_item_removed" in diff:
#         removed_items = diff["dictionary_item_removed"]
#         print("Removed items:")
#         for key in removed_items:
#             print(f"\t{key}")

#     # Handle added values
#     if "dictionary_item_added" in diff:
#         added_items = diff["dictionary_item_added"]
#         print("Added items:")
#         for key in added_items:                
#             if key.startswith("root['") and key.count("']") == 1:
#                 top_level_key = key.split("['")[1].split("']")[0]
#                 print(f"\tTop-level location added: {top_level_key}")
#                 if top_level_key in hash2:
#                     for appointment_date in hash2[top_level_key]:
#                         print(f"\t{key} => {appointment_date} => {hash2[top_level_key][appointment_date]}")

#     # Handle changed values
#     if "values_changed" in diff:
#         changed_items = diff["values_changed"]
#         print("Changed items:")
#         for key, value in changed_items.items():
#             print(f"\t{key}: {value}")

#     # Handle sublist differences
#     if "iterable_item_added" in diff:
#         added_to_sublists = diff["iterable_item_added"]
#         print("Items added to sublists:")
#         for key, value in added_to_sublists.items():
#             print(f"\t{key}: {value}")

#     if "iterable_item_removed" in diff:
#         removed_from_sublists = diff["iterable_item_removed"]
#         print("Items removed from sublists:")
#         for key, value in removed_from_sublists.items():
#             print(f"\t{key}: {value}")

#     return diff 