/* 
 This file is part of Androguard.

 Copyright (C) 2011, Anthony Desnos <desnos at t0t0.fr>
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

#include <Python.h>

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

#define METHSIM_SIGNATURE 0
#define CLASSSIM_SIGNATURE 1
#define STRING_SIGNATURE 2

#define CACHE_ELEM 10000

class Signature {
    public :
        unsigned int id;
        unsigned int type;
        float entropy;
        string value;
        vector<double> *ets;

        const char *input;
        size_t input_size;

        unsigned int link;
        unsigned int used;
};

struct resultcheck {
    unsigned int id;
    unsigned int rid;
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

ac_error_code
decref_result_object(void* item, void* data) {
    return AC_SUCCESS;
}

class Msign {
    public :
        float threshold_value_low;
        float threshold_value_high;
        int cluster_npass;
        int cluster_ncols;
        char cluster_dist;
        char cluster_method;
        double *cluster_weight;
        
        ac_index *aho;
        sparse_hash_map<Signature *, float> entropies_hashmap_sign_ncd;
        sparse_hash_map<Signature *, float> entropies_hashmap_elem;

        sparse_hash_map<string, float> ncd_hashmap;
        sparse_hash_map<string, int> compress_hashmap;

        sparse_hash_map<int, int> link_signatures;
        sparse_hash_map<int, int> old_signatures;

        vector<Signature *> vector_elem_string;

        vector<resultcheck_t *> vector_results;

        debug_t dt;
    public :
        Msign() {
            /* Default values */
            threshold_value_low = 0.2;
            threshold_value_high = 0.3;
            cluster_npass = 1;
            cluster_ncols = 0;
            cluster_dist = 'e';
            cluster_method = 'm';

            cluster_weight = NULL;

            /* Setup aho corasick */
            aho = ac_index_new();
            /* Set the default compressor : Snappy */
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


        void set_threshold_low(float value) {
            threshold_value_low = value;
            
            if (dt.log) {
                printf("THRESHOLD LOW = %f\n", value);
            }
        }
        
        void set_threshold_high(float value) {
            threshold_value_high = value;
            
            if (dt.log) {
                printf("THRESHOLD HIGH = %f\n", value);
            }
        }

        void set_npass(int value) {
            cluster_npass = value;
        }

        int add_sign_sim(unsigned int id, unsigned int id_link, unsigned int value_link, const char *input, size_t input_size, vector<double> *ets) {
            Signature *s1 = new Signature();

            s1->id = id;
            s1->type = 0;
            s1->value = string(input, input_size);
            s1->entropy = entropy( (void *)input, input_size );
            s1->ets = ets; 
            s1->link = id_link;
            s1->used = 1;

            link_signatures[ id_link ] = value_link;
            old_signatures[ id_link ] = value_link;

            if (dt.log) {
                cout << "ADD SIGN " << s1->id << " " << s1->type << " " << s1->link <<  " " << value_link << "\n";
            }
    

            entropies_hashmap_sign_ncd[ s1 ] = s1->entropy;
            
            return 0;
        }

        int add_sign_string(unsigned int id, unsigned int id_link, unsigned int value_link, const char *input, size_t input_size) {
            Signature *s1 = new Signature();
            s1->id = id;

            s1->type = 0;
            s1->value = string(input, input_size);
            s1->link = id_link;


            if (dt.log) {
                cout << "ADD SIGN STRING " << s1->id << " " << s1->type << " " << s1->link <<  " " << value_link << "\n";
            }

            ac_index_enter( aho, (ac_symbol *)input, input_size, s1 );
            
            return 0;
        }
       
        int fix() {
            /* Fix Aho Corasick algorithm */
            ac_index_fix( aho );
            return 0;
        }

        int check_string(const char *input, size_t input_size) {
            int ret = -1;

            ret = check_elem_string( input, input_size );

            return ret;
        }

        int check_sim() {
            int ret = -1;

            if (entropies_hashmap_sign_ncd.size() == 0)
                return ret;

            /* Fix Cluster */
            int nrows = entropies_hashmap_sign_ncd.size() + entropies_hashmap_elem.size();

            double** data = (double **)malloc(nrows*sizeof(double*));
            int** mask = (int **)malloc(nrows*sizeof(int*));
          
            if (data == NULL || mask == NULL)
                return -2;

            sparse_hash_map<int, Signature *> cluster_id_hashmap;

            int i = 0;
            int j = 0;
            for (i = 0; i < nrows; i++)
            { 
                data[i] = (double *)malloc(cluster_ncols*sizeof(double));
                if (data[i] == NULL)
                    return -2;

                mask[i] = (int *)malloc(cluster_ncols*sizeof(int));
                if (mask[i] == NULL)
                    return -2;
            }

            ////////////////////////////////////////////
            if (dt.log) {
                printf("ADD SIGNATURES\n");
            }

            i = 0;
            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_sign_ncd.begin(); it != entropies_hashmap_sign_ncd.end(); ++it) {
                for(unsigned int ii = 0; ii < it->first->ets->size(); ii++) {
                    data[ i ][ ii ] = (double)(*it->first->ets)[ ii ];
                    mask[ i ][ ii ] = 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }
            
            ///////////////////////////////////////////
            if (dt.log) {
                printf("ADD ELEMENTS\n");
            }

            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_elem.begin(); it != entropies_hashmap_elem.end(); ++it) {
                for(unsigned int ii = 0; ii < it->first->ets->size(); ii++) {
                    data[ i ][ ii ] = (double)(*it->first->ets)[ ii ];
                    mask[ i ][ ii ] = 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }

            /* Determine the number of clusters by using a classical formula */
            int nclusters = (int)sqrt( nrows );
            int transpose = 0;
            int ifound = 0;
            double error;
            int* clusterid = (int *)malloc(nrows*sizeof(int));


            if (clusterid == NULL) {
                return -2;
            }

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
            }

            sparse_hash_map<int, int> sign_clusters;
            vector<int> SScluster;
            
            double **distMatrix;
            distMatrix = distancematrix(nrows, cluster_ncols, data, mask, cluster_weight, 'e', 0);
            if (!distMatrix) {      
                return -2;
            }
            
            for(i=0; i<nrows; i++) {
                for(j=0; j<i; j++) {
                    if (distMatrix[i][j] == 0.0) {
                        if (cluster_id_hashmap[ i ]->type == 0 ) {
                            if (dt.log) {
                                printf("DISTMATRIX ADD CLUSTER %d\n", clusterid[i]);
                            }
                            SScluster.push_back( clusterid[i] );
                            sign_clusters[ clusterid[i] ] = 1;
                        }
                        else if (cluster_id_hashmap[ j ]->type == 0 ) {
                            if (dt.log) {
                                printf("DISTMATRIX ADD CLUSTER %d\n", clusterid[j]);
                            }
                            SScluster.push_back( clusterid[j] );
                            sign_clusters[ clusterid[j] ] = 1;    
                        }
                                                
                    }    
                }                                            
            }
                 
            for(i = 0; i < cluster_ncols; i++) 
                free(distMatrix[i]);
            free(distMatrix);

            
            ////////////////////////////////////////////////////////////////////// 

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

            for(unsigned int ii=0; ii < SScluster.size(); ii++) {
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

                for(unsigned int jj=0; jj < SSelem.size(); jj++) {
                    ret = check_elem_ncd( SSsign, SSelem[ jj ] );
                    if (ret == 0) {
                        break;
                    }
                }

                /* Ok we found a valid signature !, go out ! */
                if (ret == 0) {
                    SSsign.clear();
                    SSelem.clear();
                    break;
                }

                SSsign.clear();
                SSelem.clear();
            }
           
            for (i = 0; i < nrows; i++) {   
                free(data[i]);
                free(mask[i]);
            }

            free(data);
            free(mask);
            free(clusterid);
           
            sign_clusters.clear(); 
            SScluster.clear();

            return ret;
        }

        int check_asim() {
            int ret = -1;

            if (entropies_hashmap_sign_ncd.size() == 0)
                return ret;

            /* Fix Cluster */
            int nrows = entropies_hashmap_sign_ncd.size() + entropies_hashmap_elem.size();

            double** data = (double **)malloc(nrows*sizeof(double*));
            int** mask = (int **)malloc(nrows*sizeof(int*));
          
            if (data == NULL || mask == NULL)
                return -2;

            sparse_hash_map<int, Signature *> cluster_id_hashmap;

            int i = 0;
            for (i = 0; i < nrows; i++)
            { 
                data[i] = (double *)malloc(cluster_ncols*sizeof(double));
                if (data[i] == NULL)
                    return -2;
                
                mask[i] = (int *)malloc(cluster_ncols*sizeof(int));
                if (mask[i] == NULL)
                    return -2;
            }

            ////////////////////////////////////////////
            if (dt.log) {
                printf("ADD SIGNATURES\n");
            }

            i = 0;
            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_sign_ncd.begin(); it != entropies_hashmap_sign_ncd.end(); ++it) {
                for(unsigned int ii = 0; ii < it->first->ets->size(); ii++) {
                    data[ i ][ ii ] = (double)(*it->first->ets)[ ii ];
                    mask[ i ][ ii ] = 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }
            
            ///////////////////////////////////////////
            if (dt.log) {
                printf("ADD ELEMENTS\n");
            }

            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_elem.begin(); it != entropies_hashmap_elem.end(); ++it) {
                for(unsigned int ii = 0; ii < it->first->ets->size(); ii++) {
                    data[ i ][ ii ] = (double)(*it->first->ets)[ ii ];
                    mask[ i ][ ii ] = 1;
                }

                cluster_id_hashmap[ i ] = it->first;
                i += 1;
            }

            int nclusters = (int)sqrt( nrows );
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

            for(unsigned int ii=0; ii < SScluster.size(); ii++) {
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

                for(unsigned int jj=0; jj < SSelem.size(); jj++) {
                    check_elem_ncd_full( SSsign, SSelem[ jj ] );
                }

                SSsign.clear();
                SSelem.clear();
            }
           
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
                it->first->ets->clear();
                delete it->first->ets;

                /* RAZ element */
                delete it->first;
            }
            entropies_hashmap_elem.clear();
            
            for (sparse_hash_map<Signature *, float>::const_iterator it = entropies_hashmap_sign_ncd.begin(); it != entropies_hashmap_sign_ncd.end(); ++it) {
                it->first->used = 1;
            }

            for (sparse_hash_map<int, int>::const_iterator it = link_signatures.begin(); it != link_signatures.end(); ++it) {                                    
                 link_signatures[ it->first ] = old_signatures[ it->first ];
            }

            for (unsigned int ii=0; ii < vector_results.size(); ii++) {
                free( vector_results[ ii ] );
            }
            vector_results.clear();

            /* Clear caches */
            if (ncd_hashmap.size() > CACHE_ELEM) {
                ncd_hashmap.clear();
            }

            if (compress_hashmap.size() > CACHE_ELEM) {
                compress_hashmap.clear();
            }

            return 0;
        }
        
        int raz_results() {
            for (unsigned int ii=0; ii < vector_results.size(); ii++) {
                free( vector_results[ ii ] );
            }
            vector_results.clear();

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

        int add_elem_sim(unsigned int id, const char *input, size_t input_size, vector<double> *ets) {
            float elem_entropy = entropy( (void *)input, input_size );

            Signature *s1 = new Signature();
            s1->id = id;
            s1->type = 1;
            s1->value = string(input, input_size);
            s1->entropy = elem_entropy;
            s1->ets = ets;

            entropies_hashmap_elem[ s1 ] = s1->entropy;
            dt.elem += 1;

            return 0;
        }

        /*
        int add_elem_string(unsigned int id, const char *input, size_t input_size) {
            Signature *s1 = new Signature();

            s1->id = id;
            s1->type = 1;
            s1->input = input;
            s1->input_size = input_size;

            vector_elem_string.push_back( s1 );

            return 0;
        }
        */

        int check_elem_string(const char *input, size_t input_size) {
            int ret = -1;

            ac_list*      results;
            ac_list_item* result_item = NULL;
            ac_result*    result = NULL;

            results = ac_list_new();
            ac_index_query( aho, (ac_symbol *)input, input_size, results );
           
            result_item = results->first;
            
            while (result_item) {
                result = (ac_result*) result_item->item;
                
                Signature *s1 = (Signature *)(result->object);
                //cout << "START " << result->start << " END " << result->end << " " << s1->id << "\n";

                add_result( s1->id );
/*                r->id = s1->id;
                r->value = 0;
                r->start = result->start;
                r->end = result->end;
                r->next = NULL;                
*/
                result_item = result_item->next;
/*
                if (result_item) {
                    r->next = (resultcheck_t *)malloc( sizeof(resultcheck_t) );
                    r = r->next;
                }
*/
                ret = 0;
            }
            
            return ret;
        }

        int check_elem_ncd(vector <Signature *> SS, Signature *s1) {
            float current_value;
            float min = 1.0;
            unsigned int id;

            unsigned int ii;
            unsigned int pos_ii;
            for(ii=0; ii < SS.size(); ii++) {
                if (SS[ ii ]->used == 0)
                    continue;

                current_value = sign_ncd( s1->value, SS[ ii ]->value, 0 );
               
                //printf("ALL VAL %d(%d) %d(%d) = %f\n", SS[ii]->id, SS[ ii ]->value.length(), s1->id, s1->value.length(), current_value);
               
                if (current_value < min) {
                    min = current_value;
                    id = SS[ ii ]->id;
                    pos_ii = ii;
                }
            }

            if (min <= threshold_value_low) {
                add_result( id, min );
                SS[ pos_ii ]->used = 0;
                
                //printf("MATCH VAL %d(%d) %d(%d) = %f\n", SS[ pos_ii ]->id, SS[ pos_ii ]->value.length(), s1->id, s1->value.length(), current_value);
                link_signatures[ SS[ pos_ii ]->link ] --;
                if (link_signatures[ SS[ pos_ii ]->link ] == 0) {
                    return 0;                            
                }
            }
            else if (min <= threshold_value_high) {
                set_compress_type( TYPE_BZ2 );                                                                                                                                           
                current_value = sign_ncd( s1->value, SS[ pos_ii ]->value, 1 );
                set_compress_type( TYPE_SNAPPY );                                                                                                                                           

                if (current_value <= threshold_value_low) {
                    add_result( id, current_value );
                    SS[ pos_ii ]->used = 0;

                    //printf("MATCH VAL %d(%d) %d(%d) = %f\n", SS[ pos_ii ]->id, SS[ pos_ii ]->value.length(), s1->id, s1->value.length(), current_value);
                    link_signatures[ SS[ pos_ii ]->link ] --;
                    if (link_signatures[ SS[ pos_ii ]->link ] == 0) {
                        return 0;
                    }
                }
            }

            if ((min < 1.0) && (SS[ pos_ii ]->value.length() >= 10000)) {
                set_compress_type( TYPE_BZ2 );
                current_value = sign_ncd( s1->value, SS[ pos_ii ]->value, 1 );
                set_compress_type( TYPE_SNAPPY );

                if (current_value <= threshold_value_low) {
                    add_result( id, current_value );
                    SS[ pos_ii ]->used = 0;

                    //printf("MATCH VAL %d(%d) %d(%d) = %f\n", SS[ pos_ii ]->id, SS[ pos_ii ]->value.length(), s1->id, s1->value.length(), current_value);
                    link_signatures[ SS[ pos_ii ]->link ] --;
                    if (link_signatures[ SS[ pos_ii ]->link ] == 0) {
                        return 0;
                    }
                }
            }

            return -1;
        }

        int check_elem_ncd_full(vector <Signature *> SS, Signature *s1) {
            float current_value;

            unsigned int ii;
            for(ii=0; ii < SS.size(); ii++) {
                if (SS[ ii ]->used == 0)
                    continue;

                current_value = sign_ncd( s1->value, SS[ ii ]->value, 0 );
                if (current_value <= threshold_value_high)
                {
                    add_result( SS[ ii ]->id, s1->id, current_value );
                }
            }

            return 0;
        }
        void add_result(unsigned int id) {
            resultcheck_t *t = (resultcheck_t *)malloc( sizeof(resultcheck_t) );
            t->id = id;

            vector_results.push_back( t );
        }

        void add_result(unsigned int id, float value) {
            resultcheck_t *t = (resultcheck_t *)malloc( sizeof(resultcheck_t) );
            t->id = id;
            t->value = value;

            vector_results.push_back( t );
        }

        void add_result(unsigned int id, unsigned int idref, float value) {
            resultcheck_t *t = (resultcheck_t *)malloc( sizeof(resultcheck_t) );
            t->id = id;
            t->rid = idref;
            t->value = value;

            vector_results.push_back( t );
        }
};

/* PYTHON BINDING */
typedef struct {
    PyObject_HEAD;
    Msign *s;
} sign_MsignObject;

static void
Msign_dealloc(sign_MsignObject* self)
{
    //cout<<"Called msign dealloc\n";
    delete self->s;
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *Msign_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    sign_MsignObject *self;

    self = (sign_MsignObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->s = NULL;
    }

    return (PyObject *)self;
}

static int
Msign_init(sign_MsignObject *self, PyObject *args, PyObject *kwds)
{
    if (self != NULL) 
        self->s = new Msign();

    return 0;
}

static PyObject *Msign_set_threshold_low(sign_MsignObject *self, PyObject *args)
{
    double threshold;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "d", &threshold);
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_threshold_low( threshold );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_set_threshold_high(sign_MsignObject *self, PyObject *args)
{
    double threshold;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "d", &threshold);
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_threshold_high( threshold );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_set_dist(sign_MsignObject *self, PyObject *args)
{
    char dist;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "c", &dist);
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_dist( dist );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_set_method(sign_MsignObject *self, PyObject *args)
{
    char method;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "c", &method);
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_method( method );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_set_weight(sign_MsignObject *self, PyObject *args)
{
    PyObject *weight_list;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "O", &weight_list);
        if(!ok) return PyInt_FromLong(-1);
   
        if ( !PyList_Check( weight_list ) ) {

            return PyInt_FromLong(-1);
        }

        int list_size = PyList_Size( weight_list );
        double *datas = (double *)malloc( list_size * sizeof( double ) );

        for(int i=0; i<list_size; i++) {
            PyObject * pyvalue = 0;

            pyvalue = PyList_GetItem(weight_list, i);
            double value = PyFloat_AsDouble( pyvalue );

            datas[ i ] = value;
        }

        self->s->set_weight( datas, list_size );

        free( datas );
        return PyInt_FromLong(0);
     }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_set_npass(sign_MsignObject *self, PyObject *args)
{
    int npass;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "i", &npass );
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_npass( npass );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_add_sign_sim(sign_MsignObject *self, PyObject *args)
{
    unsigned int id, id_link, value_link;
    char *input; size_t input_size;

    PyObject *ets_list;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "iiis#O", &id, &id_link, &value_link, &input, &input_size, &ets_list );
        if(!ok) return PyInt_FromLong(-1);
 
        if ( !PyList_Check( ets_list ) ) {
            return PyInt_FromLong(-1);
        }

        vector<double> *ets_vector = new vector<double>;

        int list_size = PyList_Size( ets_list );
        for(int i=0; i<list_size; i++) {
            PyObject * pyvalue = 0;

            pyvalue = PyList_GetItem(ets_list, i);
            double value = PyFloat_AsDouble( pyvalue );

            ets_vector->push_back( value );
        }

        self->s->add_sign_sim( id, id_link, value_link, input, input_size, ets_vector );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_add_sign_string(sign_MsignObject *self, PyObject *args)
{
    unsigned int id, id_link, value_link;
    char *input; size_t input_size;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "iiis#", &id, &id_link, &value_link, &input, &input_size );
        if(!ok) return PyInt_FromLong(-1);
 
        self->s->add_sign_string( id, id_link, value_link, input, input_size );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyObject *Msign_add_elem_sim(sign_MsignObject *self, PyObject *args)
{
    unsigned int id;
    char *input; size_t input_size;

    PyObject *ets_list;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "is#O", &id, &input, &input_size, &ets_list );
        if(!ok) return PyInt_FromLong(-1);
 
        if ( !PyList_Check( ets_list ) ) {
            return PyInt_FromLong(-1);
        }

        vector<double> *ets_vector = new vector<double>;

        int list_size = PyList_Size( ets_list );
        for(int i=0; i<list_size; i++) {
            PyObject * pyvalue = 0;

            pyvalue = PyList_GetItem(ets_list, i);
            double value = PyFloat_AsDouble( pyvalue );

            ets_vector->push_back( value );
        }

        self->s->add_elem_sim( id, input, input_size, ets_vector );
        return PyInt_FromLong(0);
    }
    
    return PyInt_FromLong(-1);
}

static PyObject *Msign_check_sim(sign_MsignObject *self, PyObject *args)
{
    PyObject *check_list = PyList_New( 0 );
    
    if (self != NULL) {
        
        int ret = self->s->check_sim();

        PyList_Append( check_list, PyInt_FromLong( ret ) );

        for(unsigned int ii = 0; ii < self->s->vector_results.size(); ii++) {
            PyObject *icheck_list = PyList_New( 0 );

            PyList_Append( icheck_list, PyInt_FromLong( self->s->vector_results[ ii ]->id ) );
            PyList_Append( icheck_list, PyFloat_FromDouble( self->s->vector_results[ ii ]->value ) );

            PyList_Append( check_list, icheck_list );
        }

        return check_list;
    }

    return check_list;
}

static PyObject *Msign_check_asim(sign_MsignObject *self, PyObject *args)
{
    PyObject *check_list = PyList_New( 0 );
    
    if (self != NULL) {
        
        int ret = self->s->check_asim();
        
        PyList_Append( check_list, PyInt_FromLong( ret ) );

        for(unsigned int ii = 0; ii < self->s->vector_results.size(); ii++) {
            PyObject *icheck_list = PyList_New( 0 );

            PyList_Append( icheck_list, PyInt_FromLong( self->s->vector_results[ ii ]->id ) );
            PyList_Append( icheck_list, PyInt_FromLong( self->s->vector_results[ ii ]->rid ) );
            PyList_Append( icheck_list, PyFloat_FromDouble( self->s->vector_results[ ii ]->value ) );

            PyList_Append( check_list, icheck_list );
        }

        return check_list;
    }

    return check_list;
}

static PyObject *Msign_check_string(sign_MsignObject *self, PyObject *args)
{
    char *input; size_t input_size;
    PyObject *check_list = PyList_New( 0 );
    
    if (self != NULL) {

        int ok = PyArg_ParseTuple( args, "s#", &input, &input_size );
        if(!ok) return check_list;

        int ret = self->s->check_string( input, input_size );

        PyList_Append( check_list, PyInt_FromLong( ret ) );

        for(unsigned int ii = 0; ii < self->s->vector_results.size(); ii++) {
            PyObject *icheck_list = PyList_New( 0 );

            PyList_Append( icheck_list, PyInt_FromLong( self->s->vector_results[ ii ]->id ) );
            //PyList_Append( icheck_list, PyFloat_FromDouble( self->s->vector_results[ ii ]->value ) );

            PyList_Append( check_list, icheck_list );
        }

        return check_list;
    }

    return check_list;
}

static PyObject *Msign_get_debug(sign_MsignObject *self, PyObject *args)
{
    PyObject *debug = PyList_New( 0 );

    if (self != NULL) {
        PyList_Append( debug, PyLong_FromLong( self->s->dt.cmp ) );
        PyList_Append( debug, PyLong_FromLong( self->s->dt.elem ) );
        PyList_Append( debug, PyLong_FromLong( self->s->dt.nbclusters ) );
        PyList_Append( debug, PyLong_FromLong( self->s->dt.nbcmpclusters ) );
    }

    return debug;
}

static PyObject *Msign_raz(sign_MsignObject *self, PyObject *args)
{
    if (self != NULL) {
        self->s->raz();
        return PyInt_FromLong( 0 );
    }
    return PyInt_FromLong( -1 );
}

static PyObject *Msign_raz_results(sign_MsignObject *self, PyObject *args)
{
    if (self != NULL) {
        self->s->raz_results();
        return PyInt_FromLong( 0 );
    }
    return PyInt_FromLong( -1 );
}

static PyObject *Msign_fix(sign_MsignObject *self, PyObject *args)
{
    if (self != NULL) {
        self->s->fix();
        return PyInt_FromLong( 0 );
    }
    return PyInt_FromLong( -1 );
}

static PyObject *Msign_set_debug_log(sign_MsignObject *self, PyObject *args)
{
    int value;

    if (self != NULL) {
        
        int ok = PyArg_ParseTuple( args, "i", &value);
        if(!ok) return PyInt_FromLong(-1);
    
        self->s->set_debug_log( value );
        return PyInt_FromLong(0);
    }

    return PyInt_FromLong(-1);
}

static PyMethodDef Msign_methods[] = {
    {"set_threshold_low",  (PyCFunction)Msign_set_threshold_low, METH_VARARGS, "set threshold low" },
    {"set_threshold_high",  (PyCFunction)Msign_set_threshold_high, METH_VARARGS, "set threshold high" },
    {"set_dist",  (PyCFunction)Msign_set_dist, METH_VARARGS, "set dist" },
    {"set_method",  (PyCFunction)Msign_set_method, METH_VARARGS, "set method" },
    {"set_weight",  (PyCFunction)Msign_set_weight, METH_VARARGS, "set weight" },
    {"set_npass",  (PyCFunction)Msign_set_npass, METH_VARARGS, "set npass" },
    {"set_debug_log",  (PyCFunction)Msign_set_debug_log, METH_VARARGS, "set debug log" },
    
    {"add_sign_sim",  (PyCFunction)Msign_add_sign_sim, METH_VARARGS, "add sign sim" },
    {"add_sign_string",  (PyCFunction)Msign_add_sign_string, METH_VARARGS, "add sign string" },
    
    {"add_elem_sim",  (PyCFunction)Msign_add_elem_sim, METH_VARARGS, "add elem_sim" },
    
    {"check_sim",  (PyCFunction)Msign_check_sim, METH_VARARGS, "check sim" },
    {"check_asim",  (PyCFunction)Msign_check_asim, METH_VARARGS, "check asim" },
    {"check_string",  (PyCFunction)Msign_check_string, METH_VARARGS, "check string" },
    
    {"get_debug",  (PyCFunction)Msign_get_debug, METH_VARARGS, "get debug" },
    
    {"fix",  (PyCFunction)Msign_fix, METH_NOARGS, "fix" },
    {"raz",  (PyCFunction)Msign_raz, METH_NOARGS, "raz" },
    {"raz_results",  (PyCFunction)Msign_raz_results, METH_NOARGS, "raz_results" },

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject sign_MsignType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "sign.Msign",             /*tp_name*/
    sizeof(sign_MsignObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Msign_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "Msign objects",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    Msign_methods,             /* tp_methods */
    NULL,             /* tp_members */
    NULL,           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Msign_init,      /* tp_init */
    0,                         /* tp_alloc */
    Msign_new,                 /* tp_new */
};

PyObject *entropy(PyObject *self, PyObject* args)
{
    char *input; size_t input_size;

    int ok = PyArg_ParseTuple( args, "s#", &input, &input_size );
    if(!ok) return PyInt_FromLong(-1);

    double value = entropy( input, input_size );
   
    return PyFloat_FromDouble( value );
}

static PyMethodDef sign_methods[] = {
    {"entropy",  (PyCFunction)entropy, METH_VARARGS, "entropy" },
    {NULL}  /* Sentinel */
};

extern "C" PyMODINIT_FUNC initlibsign(void) {
    PyObject *m;

    sign_MsignType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&sign_MsignType) < 0)
        return;

    m = Py_InitModule3("libsign", sign_methods, "Example module that creates an extension type.");

    Py_INCREF(&sign_MsignType);
    PyModule_AddObject(m, "Msign", (PyObject *)&sign_MsignType);
}

#endif
