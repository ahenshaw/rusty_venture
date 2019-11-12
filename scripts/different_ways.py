from collections import Counter, defaultdict

def findPartitions(values, N):
        counts = defaultdict(list)
        counts[0] = [[]]
        for i in range(1, N+1):
            for v in values:
                diff = i - v
                if diff in counts:
                    for previous in counts[diff]:
                        new = previous.copy()
                        new.append(v)
                        counts[i].append(new)
        results = set()
        for x in (sorted(Counter(x).items()) for x in counts[N]):
            results.add(tuple(x))
        if not results:
            results = ((N,1),)
        return results

for i in range(29,30):
    print(i)
    for solution in findPartitions([6, 7, 10, 11, 12, 13], i):
        print('    ', solution)

