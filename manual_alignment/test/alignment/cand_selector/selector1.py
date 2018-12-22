#! /usr/bin/env python
# -*- coding: utf-8 -*-

def select_cand(config, align_result, range_x, range_y, range_z):
    align_result.sort(key=lambda x: x['z'])
    align_result.sort(key=lambda x: -x['score'])
    # output_z_num = [0 for z in range(len(range_z))]
    # print(range_z[-1], range_z[0])
    z_grid_num = ((range_z[-1] - range_z[0])//config.align_voxel_size[2]) + 1
    output_grid_num = [[[0]*z_grid_num for col in range(config.search_grid_size)] for row in range(config.search_grid_size)]    # output_grid_num[x][y][z]
    grid_size = [((range_x[-1] - range_x[0])//config.search_grid_size) + 1, ((range_y[-1] - range_y[0])//config.search_grid_size) + 1, config.align_voxel_size[2]]    # [x, y, z]
    print('grid size: {}'.format(grid_size))
    print('search grid divided to : {}'.format([config.search_grid_size, config.search_grid_size, z_grid_num]))

    valid_cands = []
    for cand in align_result:
        x_index = (cand['x'] - range_x[0])//grid_size[0]
        y_index = (cand['y'] - range_y[0])//grid_size[1]
        # z_index = range_z.index(-cand['z'])    # cand['z'] contains -z value
        z_index = (-cand['z'] - range_z[0])//grid_size[2]    # cand['z'] contains -z value
        # print(cand['x'] ,cand['y'] ,cand['z'], x_index, y_index, z_index)
        # if output_z_num[z_index] > max_save_znum:
        #     continue
        if output_grid_num[x_index][y_index][z_index] > config.max_save_grid_num - 1:
            continue
        if len(list(filter(lambda x: abs(cand['x'] - x['x']) < config.merge_neighbor[0] and abs(cand['y'] - x['y']) < config.merge_neighbor[1] and abs(cand['z'] - x['z']) < config.merge_neighbor[2], valid_cands))) == 0:
            valid_cands.append(cand)
            # output_z_num[z_index] += 1
            output_grid_num[x_index][y_index][z_index] += 1
    align_result = valid_cands
    
    return align_result, output_grid_num
