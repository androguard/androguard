/* 
 This file is part of Androguard.

 Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
 All rights reserved.

 Androguard is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Androguard is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of  
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Androguard.  If not, see <http://www.gnu.org/licenses/>.
*/
#ifdef __cplusplus

#include "../../../classification/libsimilarity/similarity.h"
#include "aho_corasick.h"
#include "cluster.h"
#include <math.h>

#include <iostream>
#include <google/sparse_hash_map>
#include <hash_map>
#include <string>
#include <vector>

using namespace __gnu_cxx;
using namespace std;
using google::sparse_hash_map;      // namespace where class lives by default
using std::cout;
using std::endl;

#define NCD_SIGNATURE 0
#define MPSM_SIGNATURE 1

struct entropies {
    float value;
    struct entropies *next;
};
typedef struct entropies entropies_t;

class Signature {
    public :
        unsigned int id;
        unsigned int type;
        float entropy;
        string value;
        entropies_t *ets;
};

struct resultcheck {
    unsigned int id;
    float value;
    
    unsigned int start;
    unsigned int end;

    struct resultcheck *next;
};
typedef struct resultcheck resultcheck_t;

struct debug {
    unsigned long cmp;
    unsigned long elem;

    int nbclusters;
    int nbcmpclusters;

    int log;
};

typedef struct debug debug_t;

class Msign {
    public :
        float threshold_value;
        int cluster_npass;
        int cluster_ncols;
        char cluster_dist;
        char cluster_method;
        double *cluster_weight;
        
        ac_index *aho;
        sparse_hash_map<Signature *, float> entropies_hashmap_mpsm;
        sparse_hash_map<Signature *, float> entropies_hashmap_sign_ncd;
        sparse_hash_map<Signature *, float> entropies_hashmap_elem;
        sparse_hash_map<string, float> ncd_hashmap;
        sparse_hash_map<string, int> compress_hashmap;


        debug_t dt;
    public :
        Msign() {
            threshold_value = 0.2;
            cluster_npass = 1;
            cluster_ncols = 0;
            cluster_dist = 'e';
            cluster_method = 'm';

            cluster_weight = NULL;

            aho = ac_index_new();
            set_compress_type( TYPE_SNAPPY );
            
            dt.log = 0;
            dt.cmp = 0;
            dt.elem = 0;
            dt.nbclusters = 0;
            dt.nbcmpclusters = 0;
        }

        int get_debug(debug_t *pdt) {
            pdt->cmp = dt.cmp;
            pdt->elem = dt.elem;
            pdt->nbclusters = dt.nbclusters;
            pdt->nbcmpclusters = dt.nbcmpclusters;
            pdt->log = dt.log;

            return 0;
        }

        int set_debug_log(int value) {
            if (value > 0) {
                dt.log = 1;
            } else {
                dt.log = 0;
            }

            return 0;
        }

        int set_weight(double *w, int size) {
            int i;

            if (cluster_weight != NULL) {
                free(cluster_weight);
            }

            cluster_ncols = size;
            cluster_weight = (double *)malloc(cluster_ncols*sizeof(double));

            for(i=0; i < size; i++) {
                if (dt.log) {
                    printf("ADD WEIGHT %d -> %f\n", i, w[ i ]);
                }
                cluster_weight[ i ] = w[ i ];
            }

            return 0;
        }

        int set_dist(char c) {
            cluster_dist = c;
            
            if (dt.log) {
                printf("DIST = %c\n", cluster_dist);
            }

            return 0;
        }

        int set_method(char c) {
            cluster_method = c;
            
            if (dt.log) {
                printf("METHOD = %c\n", cluster_method);
            }
            
            return 0;
        }


        void set_threshold(float value) {
            threshold_value = value;
        }

        void set_npass(int value) {
            cluster_npass = value;
        }

        int add_sign(unsigned int id, unsigned int type, const char *input, size_t input_size, entropies_t *ets) {
            if (type == NCD_SIGNATURE || type == MPSM_SIGNATURE) {
                Signature *s1 = new Signature();

                s1->id = id;
                s1->type = 0;
                s1->value = string(input, input_size);
                s1->entropy = entropy( (void *)input, input_size );
                s1->ets = (entropies_t *) malloc( sizeof(entropies_t) );
                    
                entropies_t *e = ets;
                entropies_t *e1 = s1->ets;
                while( e != NULL ) {
                    e1->value = e->value;

                    if (e->next != NULL) {
                        e1->next = (entropies_t *) malloc( sizeof(entropies_t) );
                        e1 = e1->next;
                    } else {
                        e1->next = NULL;
                    }
                    e = e->next;
                }

                if (type == NCD_SIGNATURE) {
                    entropies_hashmap_sign_ncd[ s1 ] = s1->entropy;
                }

                else if (type == MPSM_SIGNATURE) {
                    ac_index_enter( aho, (ac_symbol *)input, input_size, s1 );
                    entropies_hashmap_mpsm[ s1 ] = s1->entropy;
                }

                return 0;
            }

            return -1;
        }

        int check(resultcheck_t *rt) {
            int ret = -1;

            /* Fix Aho Corasick algorithm */
            ac_index_fix( aho );

            /* Fix Cluster */
            int nrows = entropies_hashmap_sign_ncd.size() + entropies_hashmap_elem.size();

            double** data = (double **)malloc(nrows*sizeof(double*));
            int** mask = (int **)malloc(nrows*sizeof(int*));
          
            sparse_hash_map<int, Signature *> cluster_id_hashmap;

            int j = 0;
            int i = 0;
            for (i = 0; i < nrows; i++)
            { 
                data[i] = (double *)malloc(cluster_ncols*sizeof(double));
                mask[i] = (int *)malloc(cluster_ncols*sizeof(int));
            }

            ////////////////////////////////////////////
            if (dt.log) {
                printf("ADD SIGNATURES\n");
            }

            i = 0;
            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_sign_ncd.begin(); it != entropies_hashmap_sign_ncd.end(); ++it) {
                
                entropies_t *e = it->first->ets; j = 0;
                while( e != NULL ) {
                    data[ i ][ j ] = (double)e->value;
                    mask[ i ][ j ] = 1;
                    
                    e = e->next;
                    j += 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }
            
            ///////////////////////////////////////////
            if (dt.log) {
                printf("ADD ELEMENTS\n");
            }

            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_elem.begin(); it != entropies_hashmap_elem.end(); ++it) {
                
                entropies_t *e = it->first->ets; j = 0;
                while( e != NULL ) {
                    data[ i ][ j ] = (double)e->value;
                    mask[ i ][ j ] = 1;
                    
                    e = e->next;
                    j += 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }

            int nclusters = (int)sqrt( nrows ); // + entropies_hashmap_sign_ncd.size();
            int* clusterid = (int *)malloc(nrows*sizeof(int));
            int transpose = 0;
            int ifound = 0;
            double error;


            if (dt.log) {
                printf("CLUSTERING ...\n");
            }
            
            dt.nbclusters = nclusters;
            kcluster(nclusters, nrows, cluster_ncols, data, mask, cluster_weight, transpose, cluster_npass, cluster_method, cluster_dist, clusterid, &error, &ifound);

            if (dt.log) {
                printf ("Solution found %d times; within-cluster sum of distances is %f\n", ifound, error);
                printf ("Cluster assignments:\n");
            
                for (i = 0; i < nrows; i++)
                    printf ("Sign %d: cluster %d %d\n", i, clusterid[i], cluster_id_hashmap[ i ]->id);
            /*
            int** index;
            int* count;
            */
           /*
                index = (int **)malloc(nclusters*sizeof(int*));
                count = (int *)malloc(nclusters*sizeof(int));
                for (i = 0; i < nclusters; i++) count[i] = 0;
                for (i = 0; i < nrows; i++) count[clusterid[i]]++;
                for (i = 0; i < nclusters; i++) index[i] = (int *)malloc(count[i]*sizeof(int));
                for (i = 0; i < nclusters; i++) count[i] = 0;
                for (i = 0; i < nrows; i++)
                {   int id = clusterid[i];
                    index[id][count[id]] = i;
                    count[id]++;
                } 
            */
/*
            distance = clusterdistance(nrows, ncols, data, mask, weight, count[0], count[1], index[0], index[1], 'e', 'a', 0); 
            printf("Distance between 0 and 1: %7.3f\n", distance);
            distance = clusterdistance(nrows, ncols, data, mask, weight, count[0], count[2], index[0], index[2], 'e', 'a', 0); 
  printf("Distance between 0 and 2: %7.3f\n", distance);
  distance =
    clusterdistance(nrows, ncols, data, mask, weight, count[1], count[2],
		    index[1], index[2], 'e', 'a', 0); 
  printf("Distance between 1 and 2: %7.3f\n", distance);
*/
                /*
                printf ("\n");
                printf ("------- Cluster centroids:\n");
                getclustercentroids(nclusters, nrows, ncols, data, mask, clusterid, data, mask, 0, 'a');
                printf("   Microarray:");
                for(i=0; i<ncols; i++) printf("\t%7d", i);
                printf("\n");
                for (i = 0; i < nclusters; i++)
                {   printf("Cluster %2d:", i);
                    for (j = 0; j < ncols; j++) printf("\t%7.3f", data[i][j]);
                    printf("\n");
                }
                */
            }

            sparse_hash_map<int, int> sign_clusters;
            vector<int> SScluster;
            for (i = 0; i < nrows; i++) {
                if (cluster_id_hashmap[ i ]->type == 0) {
                    if (sign_clusters.count( clusterid[i] ) == 1)
                        continue;
                    SScluster.push_back( clusterid[i] );
                    sign_clusters[ clusterid[i] ] = 1;
                }
            }

            dt.nbcmpclusters = SScluster.size();
            if (dt.log) {
                printf("CLUSTER SIZE = %d\n", SScluster.size());
            }

            int ii;
            for(ii=0; ii < SScluster.size(); ii++) {
                vector<Signature *> SSsign;
                vector<Signature *> SSelem;
                for (i = 0; i < nrows; i++) {
                    if (clusterid[i] == SScluster[ii]) {
                        if (cluster_id_hashmap[ i ]->type == 0) {
                            SSsign.push_back( cluster_id_hashmap[ i ] );
                        } else {
                            SSelem.push_back( cluster_id_hashmap[ i ] );
                        }
                    }
                }

                if (dt.log) {
                    printf("CLUSTER %d SIGN %d ELEM %d\n", SScluster[ii], SSsign.size(), SSelem.size());
                }

                int jj;
                for(jj=0; jj < SSelem.size(); jj++) {
                    ret = check_elem_ncd( SSsign, SSelem[ jj ], rt );
                    if (ret == 0) {
                        break;
                    }
                }

                if (ret == 0){
                    break;
                }

                SSsign.clear();
                SSelem.clear();
            }
           
            /*
            if (dt.log) {
                for (i = 0; i < nclusters; i++) free(index[i]);
                free(index);
                free(count);
            }*/

            for (i = 0; i < nrows; i++)
            {   free(data[i]);
                free(mask[i]);
            }
            free(data);
            free(mask);
            free(clusterid);
           
            sign_clusters.clear(); 
            SScluster.clear();

            return ret;
        }

        int raz() {
            /* RAZ debug */
            dt.cmp = 0;
            dt.elem = 0;
            dt.nbclusters = 0;
            dt.nbcmpclusters = 0;

            /* RAZ elements */
            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_elem.begin(); it != entropies_hashmap_elem.end(); ++it) {                                    
                /* RAZ entropies */
                entropies_t *e = it->first->ets;
                entropies_t *next = e;
                while( e != NULL ) {
                    next = e->next;
                    free(e);
                    e = next;
                }

                /* RAZ element */
                delete it->first;
            }
            entropies_hashmap_elem.clear();
            
            return 0;
        }

        float sign_ncd(string s1, string s2, int cache) {
            int ret;
            unsigned int corig = 0;
            unsigned int ccmp = 0;
    
            if (!cache && ncd_hashmap.count( s1 + s2 ) == 1) {
                return ncd_hashmap[ s1 + s2 ];
            }

            libsimilarity_t l1;

            l1.orig = (void *)s1.c_str();
            l1.size_orig = s1.size();

            l1.cmp = (void *)s2.c_str();
            l1.size_cmp = s2.size();

            if (!cache && compress_hashmap.count( s1 ) == 1) {
                corig = compress_hashmap[ s1 ];    
            }
    
            if (!cache && compress_hashmap.count( s2 ) == 1) {
                ccmp = compress_hashmap[ s2 ];    
            }

            l1.corig = &corig;
            l1.ccmp = &ccmp;

            ret = ncd( 9, &l1 );
            dt.cmp += 1;

            // Add value in the hash map
            if (!cache && ret == 0) {
                ncd_hashmap[ s1 + s2 ] = l1.res;
                compress_hashmap[ s1 ] = *l1.corig;
                compress_hashmap[ s2 ] = *l1.ccmp;
            }

            return l1.res;
        }

        int add_elem(unsigned int id, const char *input, size_t input_size, entropies_t *ets) {
            float elem_entropy = entropy( (void *)input, input_size );

            Signature *s1 = new Signature();
            s1->id = id;
            s1->type = 1;
            s1->value = string(input, input_size);
            s1->entropy = elem_entropy;
            s1->ets = (entropies_t *) malloc( sizeof(entropies_t) );

            entropies_t *e = ets;
            entropies_t *e1 = s1->ets;
            while( e != NULL ) {
                e1->value = e->value;

                if (e->next != NULL) {
                    e1->next = (entropies_t *) malloc( sizeof(entropies_t) );
                    e1 = e1->next;
                } else {
                    e1->next = NULL;
                }

                e = e->next;
            }

            entropies_hashmap_elem[ s1 ] = s1->entropy;
            dt.elem += 1;

            return 0;
            /*
            if (signature_type == NCD_SIGNATURE) {
                return check_elem_ncd(SS, input, input_size, rct);
            } else if (signature_type == MPSM_SIGNATURE) {
                return check_elem_mpsm(input, input_size, rct);
            }

            rct->id = 0;
            rct->value = 1.0;
            rct->next = NULL;
            return -1;*/
        }


        int check_elem_mpsm(const char *input, size_t input_size, resultcheck_t *rct) {
            ac_list*      results;
            ac_list_item* result_item = NULL;
            ac_result*    result = NULL;

            results = ac_list_new();

            ac_index_query( aho, (ac_symbol *)input, input_size, results );
           
            resultcheck_t *r = rct;
            result_item = results->first;
            
            if (result_item == NULL) {
                r->id = 0;
                r->value = 0;
                r->next = NULL;
                return -1;
            }

            while (result_item) {
                result = (ac_result*) result_item->item;
                
                Signature *s1 = (Signature *)(result->object);
                //cout << "START " << result->start << " END " << result->end << " " << s1->id << " " << s1->value << "\n";

                r->id = s1->id;
                r->value = 0;
                r->start = result->start;
                r->end = result->end;
                r->next = NULL;                

                result_item = result_item->next;

                if (result_item) {
                    r->next = (resultcheck_t *)malloc( sizeof(resultcheck_t) );
                    r = r->next;
                }
            }
            
            return 0;
        }

        int check_elem_ncd(vector <Signature *> SS, Signature *s1, resultcheck_t *rct) {
            float current_value;
            float min = 1.0;
            unsigned int id;

            int ii, pos_ii;
            for(ii=0; ii < SS.size(); ii++) {
                current_value = sign_ncd( s1->value, SS[ ii ]->value, 0 );
                //printf("VAL %d %d = %f\n", SS[ii]->id, s1->id, current_value);
                //cout << "\t" << s1->value << " VS " << SS[ ii ]->value << "\n";
                if (current_value < min) {
                    min = current_value;
                    id = SS[ ii ]->id;
                    pos_ii = ii;
                }
            }

            if (min <= threshold_value){
                rct->id = id;
                rct->value = min;
                rct->next = NULL;
                return 0;
            }

            return -1;
        }
};

extern "C" Msign *init() {
    return new Msign();
}

extern "C" int check(Msign &s, resultcheck_t *rt) {
    return s.check( rt );
}

extern "C" int raz(Msign &s) {
    return s.raz();
}

extern "C" int get_debug(Msign &s, debug_t *dt) {
    return s.get_debug( dt );
}

extern "C" int set_debug_log(Msign &s, int value) {
    return s.set_debug_log( value );
}

/* cluster */
extern "C" void set_npass(Msign &s, int value) {
    s.set_npass( value );
}

extern "C" int set_weight(Msign &s, double *w, int size) {
    return s.set_weight( w, size );
}

extern "C" int set_dist(Msign &s, char c ) {
    return s.set_dist( c );
}

extern "C" int set_method(Msign &s, char c ) {
    return s.set_method( c );
}

/* MPSM */

/* NCD */
extern "C" void set_threshold(Msign &s, float value) {
    s.set_threshold( value );
}

extern "C" int add_sign(Msign &s, unsigned int id, unsigned int type, const char *input, size_t input_size, entropies_t *ets) {
    return s.add_sign( id, type, input, input_size, ets );
}

extern "C" int add_elem(Msign &s, unsigned int id, const char *input, size_t input_size, entropies_t *ets) {
    return s.add_elem( id, input, input_size, ets );
}

#endif
