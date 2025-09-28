def overlap_range(range1, range2):
    """
    Finds overlap between two 2D ranges

    :param range1: 2 long list holding range 1
    :param range2: 2 long list holding range 2
    :return: 2 long list holding the overlaping range
    """
    # Ensure ranges are sorted so start <= end
    r1 = sorted(range1)
    r2 = sorted(range2)

    # Find the max of the starts and the min of the ends
    start_overlap = max(r1[0], r2[0])
    end_overlap = min(r1[1], r2[1])

    # Check if there is an actual overlap
    if start_overlap < end_overlap:
        return [start_overlap, end_overlap]
    else:
        return None