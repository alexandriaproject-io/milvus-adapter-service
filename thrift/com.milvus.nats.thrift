struct MilvusSegmentGetRequest {
  1: string search;                         // Search text to find similar items for
  2: optional list<string> document_ids,    // List of document IDs (plays partition role)
  3: optional i16 offset;                   // how many responses to skip
  4: optional i16 limit;                    // how many responses to return
  5: optional i16 sf;                       // Search factor ( rf or nprobe depending on the index )
}

struct MilvusSegmentUpsertPayload {
  1: string segment_text;           // Text to vectorize and save
  2: string document_id;            // Id of the document ( plays partition role )
  3: string section_id;             // Id of the section
  4: string segment_id;             // Id of the segment
}

struct MilvusSegmentDeletePayload {
  2: string document_id;            // Id of the document ( plays partition role )
  3: string section_id;             // Id of the section
  4: string segment_id;             // Id of the segment
}


struct L2SegmentSearchResult {
  1: double distance,               // Distance value
  2: string document_id,            // document_id of the result
  3: string section_id,             // section_id of the result
  4: string segment_id              // segment_id of the result
}

struct L2SegmentSearchResponse {
  1: list<L2SegmentSearchResult> results,   // List of results
  2: i32 total                              // Results count
  3: bool is_error                          // Is error or not
  4: optional string error_text             // Error message text
}

struct L2SegmentUpsertResponse {
    1: i32 insert_count             // Inserted segments
    2: i32 update_count            // Updated segments
    3: i32 delete_count             // Deleted segments
    4: bool is_error                // Is error or not
    5: optional string error_text   // Error message text
}

struct L2SegmentDeleteResponse {
    1: i32 delete_count             // Deleted segments
    3: bool is_error                // Is error or not
    4: optional string error_text   // Error message text
}

