#!/usr/bin/env python
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Evaluation script')
    parser.add_argument('--org_file', required=True, type=str, help='directory of org kml file')
    parser.add_argument('--dst_file', required=True, type=str, help='directory of des kml file')
    parser.add_argument('--begin', required=True, type=str, help='begin pattern')
    parser.add_argument('--end', required=True, type=str, help='end pattern')
    args = parser.parse_args()

    org_file = args.org_file
    dst_file = args.dst_file
    begin = args.begin
    end = args.end

    lines = []
    # Find tags.
    with open(org_file) as fp:
        for cnt, line in enumerate(fp):
            lines.append(line)

    with open(dst_file, 'w') as writer:
        # Tags.
        ind = 0
        for ind in range(len(lines)):
            writer.write(lines[ind])
            if lines[ind].find('<coordinates>') > 0:
                break
        # Trj.
        is_eval = False
        for ind in range(ind, len(lines)):
            if lines[ind].find(begin) > 0:
                is_eval = True
            if is_eval is True:
                writer.write(lines[ind])
            if is_eval is True and lines[ind].find(end) > 0:
                break
        # Tags.
        is_tag = False
        for ind in range(ind, len(lines)):
            if lines[ind].find('</coordinates>') > 0:
                is_tag = True
            if is_tag is True:
                writer.write(lines[ind])

