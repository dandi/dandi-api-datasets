#!/usr/bin/env python3

import sys                                                                                                                      
from dandi.dandiarchive import navigate_url                                                                                     
from dandi.metadata import migrate2newschema                                                                                    

if __name__ == "__main__":                                                                                                      
    for ds in sys.argv[1:]:                                                                                                     
        with navigate_url(f'https://identifiers.org/DANDI:{ds}') as (client, dandiset, assets):                                 
            dandiset_meta = dandiset['metadata']                                                                                
        new_meta = migrate2newschema(dandiset_meta)                                                                             
        print(new_meta)  
