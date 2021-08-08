# hashtable implementation with user definable number of slots and using singly linked lists for tiebreaking on hash
# collisions; as a result, theoretical O(n) = n but in practice should be effectively O(n) = 1 so long as a reasonable
# number of slots are chosen to increase entropy and the internal hashing function distributes to slots reasonably well
class HashTable:
    # class constructor
    # O(n) = 1
    def __init__(self, numslots):
        self.numentries = 0  # not used internally, but potentially useful for anything that uses this class
        self.numslots = numslots  # how many slots the keys can be distributed among; recommend at least 2 * N elements
        self.slots = [None] * numslots

    # private function for generating an evenly distributed hash value, modulo the number of slots in the instance
    def __hash(self, key):
        hashsum = 0
        i = len(key) + 1

        for element in range(0, len(key)):
            # this exponent seems to give reasonably good results and does a decent job of making character order matter
            hashsum = (hashsum + (i ** ord(key[element]))) % self.numslots
            i += 1

        return hashsum

    # set a value in the hashtable, putting it into a slot based on hash function
    def set(self, key, val):
        hashkey = self.__hash(key)
        entry = self.slots[hashkey]

        if entry is None:
            self.slots[hashkey] = HashTableEntry(key, val)
            self.numentries += 1
        else:
            while True:
                if (entry.key == key):
                    entry.val = val
                    return
                # tiebreaking is done as a singly linked list
                elif (entry.next is None):
                    entry.next = HashTableEntry(key, val)
                    self.numentries += 1
                    return
                else:
                    entry = entry.next

    # unset a value set for a key, if present
    def unset(self, key):
        hashkey = self.__hash(key)
        entry = self.slots[hashkey]
        preventry = None

        # hash slot is empty, so it is obviously not in the hashtable
        if entry is None:
            return
        else:
            # find the entry in the slot; tiebreaking is done as a singly linked list; keep track of previous entry
            while entry is not None and entry.key != key:
                preventry = entry
                entry = entry.next

            if entry is not None:
                if preventry is not None:
                    # remove from the linked list
                    preventry.next = entry.next
                else:
                    # last element, so clear the slot
                    self.slots[hashkey] = None
                self.numentries -= 1

    # get the value set for a key, if present
    def get(self, key):
        hashkey = self.__hash(key)
        entry = self.slots[hashkey]

        # hash slot is empty, so it is obviously not in the hashtable
        if entry is None:
            return None
        else:
            # find the entry in the slot; tiebreaking is done as a singly linked list
            while entry is not None and entry.key != key:
                entry = entry.next

            # return entry if found
            if entry is not None:
                return entry.val
            else:
                return None

# helper class for creating singly linked lists in hashtable slots
class HashTableEntry:
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.next = None