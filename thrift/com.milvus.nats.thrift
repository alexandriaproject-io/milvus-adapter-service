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
  1: double distance,
  2: string document_id,
  3: string section_id,
  4: string segment_id
}

struct L2SegmentSearchResponse {
  2: list<list<L2SegmentSearchResult>> results,
  3: i32 total
}

struct L2SegmentSearchErrorResponse {
  1: string error_text      // Error message text
  2: string error_id        // Id of the error as appears in the service logs
}

struct L2SegmentSearchUpsertResponse {
    1: i32 insert_count     // Inserted segments
    2: i32 updated_count    // Updated segments
}


