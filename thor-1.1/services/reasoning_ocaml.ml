(** Comprehensive reasoning engine in OCaml - backup/secondary backend
    Extensive implementation with multi-topic support, knowledge synthesis,
    and advanced reasoning capabilities *)

open Str
open Unix

(******************************************************************************)
(* Types and Data Structures *)
(******************************************************************************)

type reasoning_type =
  | Causal
  | Logical
  | Mathematical
  | Comparative
  | Analytical
  | Temporal
  | Spatial
  | Inductive
  | Deductive
  | Abductive
  | General

type domain =
  | Science
  | Economics
  | Technology
  | Environment
  | Politics
  | Health
  | Education
  | History
  | Philosophy
  | GeneralDomain

type relationship_type =
  | CausalRel
  | HierarchicalRel
  | AssociativeRel
  | ComparativeRel
  | TemporalRel
  | SpatialRel

type knowledge_item = {
  topic : string;
  title : string;
  content : string;
  source : string;
  confidence : float;
  domain : domain;
}

type topic_info = {
  topic_name : string;
  domain : domain;
  relevance_score : float;
  knowledge_items : knowledge_item list;
}

type relationship = {
  topic1 : string;
  topic2 : string;
  rel_type : relationship_type;
  strength : float;
  confidence : float;
  evidence : string;
}

type reasoning_step = {
  step_number : int;
  description : string;
  reasoning : string;
  confidence : float;
  evidence : string list;
  sub_steps : reasoning_step list;
  dependencies : int list;
  knowledge_used : knowledge_item list;
}

type reasoning_chain = {
  query : string;
  reasoning_type : reasoning_type;
  steps : reasoning_step list;
  conclusion : string;
  confidence : float;
  verification_result : bool;
  quality_score : float;
  topics_involved : string list;
  relationships : relationship list;
}

type query_analysis = {
  original_query : string;
  intent : string;
  complexity : float;
  reasoning_type : reasoning_type;
  domains : domain list;
  topics : string list;
  requires_multi_topic : bool;
}

type synthesis_result = {
  synthesized_context : string;
  relationships : relationship list;
  conflicts : string list;
  quality_score : float;
  topics_covered : string list;
  total_items : int;
}

(******************************************************************************)
(* Utility Functions *)
(******************************************************************************)

(** Helper: check if string contains substring *)
let contains_substring (haystack : string) (needle : string) : bool =
  try
    let len_h = String.length haystack in
    let len_n = String.length needle in
    if len_n = 0 then true
    else if len_n > len_h then false
    else
      let rec check i =
        if i + len_n > len_h then false
        else if String.sub haystack i len_n = needle then true
        else check (i + 1)
      in
      check 0
  with _ -> false

(** Split string into words *)
let split_words (s : string) : string list =
  let rec split acc current i =
    if i >= String.length s then
      if current = "" then List.rev acc else List.rev (current :: acc)
    else
      let c = s.[i] in
      if c = ' ' || c = '\t' || c = '\n' then
        if current = "" then split acc "" (i + 1)
        else split (current :: acc) "" (i + 1)
      else
        split acc (current ^ String.make 1 c) (i + 1)
  in
  split [] "" 0

(** Count word occurrences in string *)
let count_word_occurrences (text : string) (word : string) : int =
  let rec count acc i =
    if i + String.length word > String.length text then acc
    else if String.sub text i (String.length word) = word then
      count (acc + 1) (i + 1)
    else count acc (i + 1)
  in
  count 0 0

(** Extract words of minimum length *)
let extract_meaningful_words (text : string) (min_len : int) : string list =
  let words = split_words text in
  List.filter (fun w -> String.length w >= min_len) words

(** Calculate string similarity (simple Jaccard) *)
let string_similarity (s1 : string) (s2 : string) : float =
  let words1 = extract_meaningful_words (String.lowercase_ascii s1) 3 in
  let words2 = extract_meaningful_words (String.lowercase_ascii s2) 3 in
  let set1 = List.sort_uniq compare words1 in
  let set2 = List.sort_uniq compare words2 in
  let intersection = List.filter (fun w -> List.mem w set2) set1 in
  let union = List.sort_uniq compare (words1 @ words2) in
  if List.length union = 0 then 0.0
  else float_of_int (List.length intersection) /. float_of_int (List.length union)

(** Normalize confidence score to [0.0, 1.0] *)
let normalize_confidence (score : float) : float =
  if score < 0.0 then 0.0
  else if score > 1.0 then 1.0
  else score

(** Calculate average of float list *)
let average_float (values : float list) : float =
  if List.length values = 0 then 0.0
  else
    let sum = List.fold_left (fun acc v -> acc +. v) 0.0 values in
    sum /. float_of_int (List.length values)

(** Take first n elements from list *)
let list_take (n : int) (lst : 'a list) : 'a list =
  let rec take acc remaining count =
    if count <= 0 || remaining = [] then List.rev acc
    else take (List.hd remaining :: acc) (List.tl remaining) (count - 1)
  in
  take [] lst n

(** Safe assoc lookup *)
let list_assoc_opt (key : 'a) (lst : ('a * 'b) list) : 'b option =
  try Some (List.assoc key lst)
  with Not_found -> None

(** Remove association from list *)
let list_remove_assoc (key : 'a) (lst : ('a * 'b) list) : ('a * 'b) list =
  List.filter (fun (k, _) -> k <> key) lst

(******************************************************************************)
(* Domain Classification *)
(******************************************************************************)

let classify_domain (text : string) : domain =
  let text_lower = String.lowercase_ascii text in
  let science_keywords = ["science", "physics", "chemistry", "biology", "research", 
                         "experiment", "theory", "hypothesis", "discovery"] in
  let economics_keywords = ["economics", "economic", "economy", "market", "trade",
                           "finance", "financial", "policy", "inflation", "gdp"] in
  let tech_keywords = ["technology", "tech", "computer", "software", "hardware",
                      "digital", "internet", "network", "system", "platform"] in
  let env_keywords = ["climate", "environment", "environmental", "pollution",
                     "carbon", "emission", "green", "sustainable", "renewable"] in
  let politics_keywords = ["politics", "political", "government", "policy", "law",
                          "legislation", "democracy", "election", "vote"] in
  let health_keywords = ["health", "medical", "medicine", "disease", "treatment",
                       "patient", "doctor", "hospital", "symptom"] in
  let education_keywords = ["education", "learning", "teaching", "school",
                          "university", "student", "teacher", "curriculum"] in
  let history_keywords = ["history", "historical", "war", "battle", "empire",
                        "ancient", "medieval", "revolution", "civilization"] in
  let philosophy_keywords = ["philosophy", "philosophical", "ethics", "moral",
                            "existence", "reality", "consciousness", "truth"] in
  
  let count_matches keywords =
    List.fold_left (fun acc kw -> 
      if contains_substring text_lower kw then acc + 1 else acc
    ) 0 keywords
  in
  
  let scores = [
    (Science, count_matches science_keywords);
    (Economics, count_matches economics_keywords);
    (Technology, count_matches tech_keywords);
    (Environment, count_matches env_keywords);
    (Politics, count_matches politics_keywords);
    (Health, count_matches health_keywords);
    (Education, count_matches education_keywords);
    (History, count_matches history_keywords);
    (Philosophy, count_matches philosophy_keywords);
  ] in
  
  let max_score = List.fold_left (fun acc (_, score) -> max acc score) 0 scores in
  if max_score = 0 then GeneralDomain
  else
    let (domain, _) = List.find (fun (_, score) -> score = max_score) scores in
    domain

(******************************************************************************)
(* Query Analysis *)
(******************************************************************************)

let analyze_query (query : string) : query_analysis =
  let query_lower = String.lowercase_ascii query in
  let word_count = List.length (split_words query) in
  
  (* Detect intent *)
  let intent = 
    if contains_substring query_lower "what is" || contains_substring query_lower "what are" then
      "definition"
    else if contains_substring query_lower "how" then
      "how_to"
    else if contains_substring query_lower "why" then
      "causal_explanation"
    else if contains_substring query_lower "compare" || contains_substring query_lower "versus" then
      "comparison"
    else if contains_substring query_lower "explain" then
      "explanation"
    else
      "general"
  in
  
  (* Calculate complexity *)
  let complexity = 
    let base = 0.3 in
    let word_factor = min (float_of_int word_count /. 20.0) 0.4 in
    let question_factor = if String.contains query '?' then 0.2 else 0.0 in
    let multi_topic_factor = 
      if contains_substring query_lower "and" || contains_substring query_lower "between" then 0.1
      else 0.0
    in
    normalize_confidence (base +. word_factor +. question_factor +. multi_topic_factor)
  in
  
  (* Detect reasoning type *)
  let reasoning_type = 
    if contains_substring query_lower "cause" || contains_substring query_lower "effect" ||
       contains_substring query_lower "why" || contains_substring query_lower "how does" then
      Causal
    else if contains_substring query_lower "if" || contains_substring query_lower "then" ||
            contains_substring query_lower "logic" || contains_substring query_lower "therefore" then
      Logical
    else if contains_substring query_lower "calculate" || contains_substring query_lower "solve" ||
            contains_substring query_lower "math" || contains_substring query_lower "equation" then
      Mathematical
    else if contains_substring query_lower "compare" || contains_substring query_lower "versus" ||
            contains_substring query_lower "difference" || contains_substring query_lower "better" then
      Comparative
    else if contains_substring query_lower "analyze" || contains_substring query_lower "examine" ||
            contains_substring query_lower "evaluate" then
      Analytical
    else if contains_substring query_lower "before" || contains_substring query_lower "after" ||
            contains_substring query_lower "during" || contains_substring query_lower "when" then
      Temporal
    else if contains_substring query_lower "where" || contains_substring query_lower "location" ||
            contains_substring query_lower "place" then
      Spatial
    else
      General
  in
  
  (* Extract domains *)
  let domains = [classify_domain query] in
  
  (* Extract topics (simple heuristic) *)
  let topics = 
    let words = extract_meaningful_words query_lower 4 in
    let stop_words = ["what", "how", "why", "when", "where", "which", "who",
                     "does", "do", "is", "are", "the", "a", "an", "and", "or"] in
    List.filter (fun w -> not (List.mem w stop_words)) words
  in
  
  (* Check if multi-topic *)
  let requires_multi_topic = 
    List.length topics >= 2 ||
    contains_substring query_lower "affect" ||
    contains_substring query_lower "impact" ||
    contains_substring query_lower "influence" ||
    contains_substring query_lower "relationship between" ||
    contains_substring query_lower "connection between"
  in
  
  {
    original_query = query;
    intent;
    complexity;
    reasoning_type;
    domains;
    topics;
    requires_multi_topic;
  }

(******************************************************************************)
(* Topic Extraction *)
(******************************************************************************)

let extract_topics (query : string) (max_topics : int) : topic_info list =
  let analysis = analyze_query query in
  let topics = list_take max_topics analysis.topics in
  
  List.map (fun topic ->
    {
      topic_name = topic;
      domain = classify_domain topic;
      relevance_score = 0.7; (* Base score *)
      knowledge_items = [];
    }
  ) topics

(******************************************************************************)
(* Relationship Detection *)
(******************************************************************************)

let detect_relationships 
    (topic1 : string) 
    (topic2 : string) 
    (content : string) 
    : relationship list =
  let content_lower = String.lowercase_ascii content in
  let topic1_lower = String.lowercase_ascii topic1 in
  let topic2_lower = String.lowercase_ascii topic2 in
  
  let relationships = ref [] in
  
  (* Causal relationships *)
  if contains_substring content_lower "causes" ||
     contains_substring content_lower "leads to" ||
     contains_substring content_lower "results in" ||
     contains_substring content_lower "affects" ||
     contains_substring content_lower "impacts" then
    if contains_substring content_lower topic1_lower &&
       contains_substring content_lower topic2_lower then
      relationships := {
        topic1;
        topic2;
        rel_type = CausalRel;
        strength = 0.7;
        confidence = 0.6;
        evidence = Printf.sprintf "%s affects %s" topic1 topic2;
      } :: !relationships;
  
  (* Hierarchical relationships *)
  if contains_substring content_lower "is a type of" ||
     contains_substring content_lower "is part of" ||
     contains_substring content_lower "belongs to" ||
     contains_substring content_lower "contains" ||
     contains_substring content_lower "includes" then
    if contains_substring content_lower topic1_lower &&
       contains_substring content_lower topic2_lower then
      relationships := {
        topic1;
        topic2;
        rel_type = HierarchicalRel;
        strength = 0.6;
        confidence = 0.5;
        evidence = Printf.sprintf "%s is related to %s" topic1 topic2;
      } :: !relationships;
  
  (* Associative relationships *)
  if contains_substring content_lower "related to" ||
     contains_substring content_lower "associated with" ||
     contains_substring content_lower "connected to" ||
     contains_substring content_lower "linked to" then
    if contains_substring content_lower topic1_lower &&
       contains_substring content_lower topic2_lower then
      relationships := {
        topic1;
        topic2;
        rel_type = AssociativeRel;
        strength = 0.5;
        confidence = 0.5;
        evidence = Printf.sprintf "%s is associated with %s" topic1 topic2;
      } :: !relationships;
  
  (* Comparative relationships *)
  if contains_substring content_lower "compared to" ||
     contains_substring content_lower "versus" ||
     contains_substring content_lower "vs" ||
     contains_substring content_lower "different from" ||
     contains_substring content_lower "similar to" then
    if contains_substring content_lower topic1_lower &&
       contains_substring content_lower topic2_lower then
      relationships := {
        topic1;
        topic2;
        rel_type = ComparativeRel;
        strength = 0.6;
        confidence = 0.5;
        evidence = Printf.sprintf "%s compared to %s" topic1 topic2;
      } :: !relationships;
  
  !relationships

(******************************************************************************)
(* Knowledge Synthesis *)
(******************************************************************************)

let synthesize_knowledge 
    (knowledge_by_topic : (string * knowledge_item list) list)
    (query : string)
    (previous_context : string option)
    : synthesis_result =
  
  (* Collect all knowledge items *)
  let all_items = 
    List.fold_left (fun acc (_, items) -> items @ acc) [] knowledge_by_topic
  in
  
  (* Detect relationships *)
  let relationships = ref [] in
  let topics = List.map fst knowledge_by_topic in
  
  (* Check relationships between topic pairs *)
  for i = 0 to List.length topics - 1 do
    for j = i + 1 to List.length topics - 1 do
      let topic1 = List.nth topics i in
      let topic2 = List.nth topics j in
      let items1 = List.assoc topic1 knowledge_by_topic in
      let items2 = List.assoc topic2 knowledge_by_topic in
      
      (* Check relationships in content *)
      List.iter (fun item1 ->
        List.iter (fun item2 ->
          let rels = detect_relationships topic1 topic2 item1.content in
          relationships := rels @ !relationships
        ) items2
      ) items1
    done
  done;
  
  (* Build synthesized context *)
  let context_parts = ref [] in
  
  (* Add previous context if available *)
  (match previous_context with
   | Some ctx -> context_parts := ("Previous context: " ^ ctx) :: !context_parts
   | None -> ());
  
  (* Add knowledge by topic *)
  List.iter (fun (topic, items) ->
    if List.length items > 0 then (
      context_parts := (Printf.sprintf "Knowledge about '%s':" topic) :: !context_parts;
      List.iter (fun item ->
        let snippet = 
          if String.length item.content > 200 then
            String.sub item.content 0 200 ^ "..."
          else item.content
        in
        context_parts := 
          (Printf.sprintf "  [%s] %s: %s" item.source item.title snippet) :: !context_parts
      ) (list_take 3 items); (* Max 3 items per topic *)
      context_parts := "" :: !context_parts
    )
  ) knowledge_by_topic;
  
  (* Add relationships *)
  if List.length !relationships > 0 then (
    context_parts := "Relationships between topics:" :: !context_parts;
    List.iter (fun rel ->
      let rel_type_str = match rel.rel_type with
        | CausalRel -> "causal"
        | HierarchicalRel -> "hierarchical"
        | AssociativeRel -> "associative"
        | ComparativeRel -> "comparative"
        | TemporalRel -> "temporal"
        | SpatialRel -> "spatial"
      in
      context_parts := 
        (Printf.sprintf "  - %s %s %s" rel.topic1 rel_type_str rel.topic2) :: !context_parts
    ) (list_take 5 !relationships); (* Max 5 relationships *)
    context_parts := "" :: !context_parts
  );
  
  let synthesized_context = String.concat "\n" (List.rev !context_parts) in
  
  (* Calculate quality score *)
  let quality_score = 
    let context_length = String.length synthesized_context in
    let length_score = 
      if context_length >= 200 && context_length <= 2000 then 0.3
      else if context_length > 200 then 0.2
      else 0.1
    in
    let relationship_score = 
      min (float_of_int (List.length !relationships) *. 0.1) 0.3
    in
    let coverage_score = 
      if List.length all_items >= 3 then 0.2
      else if List.length all_items >= 1 then 0.1
      else 0.0
    in
    normalize_confidence (length_score +. relationship_score +. coverage_score)
  in
  
  (* Detect conflicts (simplified) *)
  let conflicts = ref [] in
  (* Simple conflict detection: look for contradictory statements *)
  List.iter (fun item1 ->
    List.iter (fun item2 ->
      if item1.topic = item2.topic && item1.content <> item2.content then
        let similarity = string_similarity item1.content item2.content in
        if similarity < 0.3 then
          conflicts := 
            (Printf.sprintf "Conflict between %s and %s" item1.title item2.title) :: !conflicts
    ) all_items
  ) all_items;
  
  {
    synthesized_context;
    relationships = !relationships;
    conflicts = !conflicts;
    quality_score;
    topics_covered = topics;
    total_items = List.length all_items;
  }

(******************************************************************************)
(* Query Decomposition *)
(******************************************************************************)

let decompose_causal_query (query : string) : reasoning_step list =
  let query_lower = String.lowercase_ascii query in
  let is_multi_topic = 
    contains_substring query_lower "affect" ||
    contains_substring query_lower "impact" ||
    contains_substring query_lower "influence"
  in
  
  if is_multi_topic then
    [
      { step_number = 1; description = "Identify the initial cause or factor"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = []; knowledge_used = [] };
      { step_number = 2; description = "Identify the affected domain or outcome"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = [1]; knowledge_used = [] };
      { step_number = 3; description = "Retrieve knowledge about the causal mechanism"; 
        reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
        dependencies = [1; 2]; knowledge_used = [] };
      { step_number = 4; description = "Evaluate the causal relationship between domains"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = [3]; knowledge_used = [] };
      { step_number = 5; description = "Assess evidence and strength of causal link"; 
        reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
        dependencies = [4]; knowledge_used = [] };
      { step_number = 6; description = "Determine the complete causal chain"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = [5]; knowledge_used = [] };
    ]
  else
    [
      { step_number = 1; description = "Identify potential causes"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = []; knowledge_used = [] };
      { step_number = 2; description = "Evaluate causal relationships"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = [1]; knowledge_used = [] };
      { step_number = 3; description = "Assess evidence strength"; 
        reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
        dependencies = [2]; knowledge_used = [] };
      { step_number = 4; description = "Determine most likely cause"; 
        reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
        dependencies = [3]; knowledge_used = [] };
    ]

let decompose_logical_query (query : string) : reasoning_step list =
  [
    { step_number = 1; description = "Identify the logical premises"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; description = "Determine the logical relationship"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; description = "Apply logical rules"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [2]; knowledge_used = [] };
    { step_number = 4; description = "Draw logical conclusion"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ]

let decompose_mathematical_query (query : string) : reasoning_step list =
  [
    { step_number = 1; description = "Parse mathematical expressions"; 
      reasoning = ""; confidence = 0.9; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; description = "Choose appropriate method"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; description = "Perform calculations"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [2]; knowledge_used = [] };
    { step_number = 4; description = "Verify result"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ]

let decompose_comparative_query (query : string) : reasoning_step list =
  [
    { step_number = 1; description = "Identify items to compare"; 
      reasoning = ""; confidence = 0.9; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; description = "Determine comparison criteria"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; description = "Evaluate each criterion"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [2]; knowledge_used = [] };
    { step_number = 4; description = "Synthesize comparison results"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ]

let decompose_analytical_query (query : string) : reasoning_step list =
  [
    { step_number = 1; description = "Break down the subject into components"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; description = "Analyze each component"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; description = "Identify patterns and relationships"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [2]; knowledge_used = [] };
    { step_number = 4; description = "Synthesize findings"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ]

let decompose_general_query (query : string) : reasoning_step list =
  [
    { step_number = 1; description = "Understand the query requirements"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; description = "Gather relevant information"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; description = "Process and analyze information"; 
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [2]; knowledge_used = [] };
    { step_number = 4; description = "Formulate response"; 
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ]

(******************************************************************************)
(* Step Reasoning Generation *)
(******************************************************************************)

let generate_step_reasoning 
    (query : string) 
    (step : reasoning_step) 
    (previous_steps : reasoning_step list)
    (knowledge_items : knowledge_item list)
    : string =
  
  let desc_lower = String.lowercase_ascii step.description in
  
  (* Build context from previous steps *)
  let previous_context = 
    if List.length previous_steps > 0 then
      let last_step = List.hd (List.rev previous_steps) in
      Printf.sprintf "Building on: %s" last_step.reasoning
    else
      ""
  in
  
  (* Extract key information from knowledge *)
  let knowledge_context = 
    if List.length knowledge_items > 0 then
      let item = List.hd knowledge_items in
      let snippet = 
        if String.length item.content > 100 then
          String.sub item.content 0 100 ^ "..."
        else item.content
      in
      Printf.sprintf "Knowledge: %s" snippet
    else
      ""
  in
  
  (* Generate reasoning based on step type *)
  if contains_substring desc_lower "identify" then
    Printf.sprintf "To answer '%s', I need to first %s. %s %s"
      query step.description previous_context knowledge_context
  else if contains_substring desc_lower "evaluate" ||
          contains_substring desc_lower "analyze" then
    Printf.sprintf "For this step, I %s by considering relevant factors and evidence. %s %s"
      (String.lowercase_ascii step.description) previous_context knowledge_context
  else if contains_substring desc_lower "apply" then
    Printf.sprintf "I %s the appropriate method based on the problem requirements. %s"
      (String.lowercase_ascii step.description) knowledge_context
  else if contains_substring desc_lower "determine" then
    Printf.sprintf "Based on the analysis so far, I can %s. %s %s"
      (String.lowercase_ascii step.description) previous_context knowledge_context
  else if contains_substring desc_lower "synthesize" ||
          contains_substring desc_lower "conclusion" then
    Printf.sprintf "I %s by combining insights from all previous steps. %s"
      (String.lowercase_ascii step.description) previous_context
  else
    Printf.sprintf "This step involves %s to progress toward the answer. %s %s"
      (String.lowercase_ascii step.description) previous_context knowledge_context

(******************************************************************************)
(* Confidence Assessment *)
(******************************************************************************)

let assess_step_confidence 
    (step : reasoning_step) 
    (knowledge_items : knowledge_item list)
    : float =
  
  let base_confidence = step.confidence in
  
  (* Increase confidence if step has evidence *)
  let evidence_bonus = 
    if List.length step.evidence > 0 then 0.1 else 0.0
  in
  
  (* Increase confidence if step has sub-steps *)
  let substep_bonus = 
    if List.length step.sub_steps > 0 then 0.1 else 0.0
  in
  
  (* Adjust based on knowledge availability *)
  let knowledge_bonus = 
    if List.length knowledge_items > 0 then 0.1 else 0.0
  in
  
  (* Calculate average knowledge confidence *)
  let knowledge_confidence = 
    if List.length knowledge_items > 0 then
      let confidences = List.map (fun item -> item.confidence) knowledge_items in
      average_float confidences *. 0.1
    else 0.0
  in
  
  normalize_confidence 
    (base_confidence +. evidence_bonus +. substep_bonus +. 
     knowledge_bonus +. knowledge_confidence)

(******************************************************************************)
(* Conclusion Synthesis *)
(******************************************************************************)

let synthesize_conclusion 
    (steps : reasoning_step list) 
    (query : string) 
    (rtype : reasoning_type) 
    : string =
  
  if List.length steps = 0 then
    "I cannot provide a definitive answer based on the available information."
  else (
    (* Combine insights from all steps *)
    let insights = 
      List.fold_right (fun step acc -> 
        if step.reasoning <> "" then step.reasoning :: acc else acc
      ) steps []
    in
    
    match rtype with
    | Causal -> 
        Printf.sprintf "The most likely cause is: %s" 
          (String.concat ". " insights)
    | Logical -> 
        Printf.sprintf "Logically following the premises: %s" 
          (String.concat ". " insights)
    | Mathematical -> 
        Printf.sprintf "Based on the mathematical analysis: %s" 
          (String.concat ". " insights)
    | Comparative -> 
        Printf.sprintf "After comparing all aspects: %s" 
          (String.concat ". " insights)
    | Analytical -> 
        Printf.sprintf "Analysis conclusion: %s" 
          (String.concat ". " insights)
    | Temporal -> 
        Printf.sprintf "Temporal analysis shows: %s" 
          (String.concat ". " insights)
    | Spatial -> 
        Printf.sprintf "Spatial analysis indicates: %s" 
          (String.concat ". " insights)
    | Inductive -> 
        Printf.sprintf "Inductive reasoning suggests: %s" 
          (String.concat ". " insights)
    | Deductive -> 
        Printf.sprintf "Deductive reasoning concludes: %s" 
          (String.concat ". " insights)
    | Abductive -> 
        Printf.sprintf "The best explanation is: %s" 
          (String.concat ". " insights)
    | General -> 
        Printf.sprintf "Based on the analysis: %s" 
          (String.concat ". " insights)
  )

(******************************************************************************)
(* Reasoning Chain Verification *)
(******************************************************************************)

let verify_reasoning_chain 
    (steps : reasoning_step list) 
    (conclusion : string) 
    : bool =
  
  if List.length steps = 0 then false
  else (
    (* Check if all steps have reasoning *)
    let has_reasoning = 
      List.for_all (fun step -> step.reasoning <> "") steps
    in
    
    (* Check if confidence scores are reasonable *)
    let avg_confidence = 
      let confidences = List.map (fun step -> step.confidence) steps in
      average_float confidences
    in
    let reasonable_confidence = avg_confidence > 0.6 in
    
    (* Check if conclusion is coherent *)
    let conclusion_coherent = String.length conclusion > 10 in
    
    (* Check step dependencies are satisfied *)
    let dependencies_satisfied = 
      let rec check_deps step_num deps =
        match deps with
        | [] -> true
        | dep :: rest ->
            if dep < step_num then check_deps step_num rest
            else false
      in
      let rec check_all steps idx =
        match steps with
        | [] -> true
        | step :: rest ->
            if check_deps idx step.dependencies then
              check_all rest (idx + 1)
            else false
      in
      check_all steps 1
    in
    
    has_reasoning && reasonable_confidence && conclusion_coherent && dependencies_satisfied
  )

(******************************************************************************)
(* Quality Score Calculation *)
(******************************************************************************)

let calculate_reasoning_quality 
    (steps : reasoning_step list) 
    (conclusion : string)
    (verification_result : bool)
    : float =
  
  if List.length steps = 0 then 0.0
  else (
    (* Base score from verification *)
    let base_score = if verification_result then 0.5 else 0.2 in
    
    (* Score based on number of steps *)
    let max_steps = 10 in
    let step_score = 
      min (float_of_int (List.length steps) /. float_of_int max_steps) 1.0 *. 0.2
    in
    
    (* Score based on average confidence *)
    let avg_confidence = 
      let confidences = List.map (fun step -> step.confidence) steps in
      average_float confidences
    in
    let confidence_score = avg_confidence *. 0.3 in
    
    normalize_confidence (base_score +. step_score +. confidence_score)
  )

(******************************************************************************)
(* Main Reasoning Chain Generation *)
(******************************************************************************)

let generate_reasoning_chain 
    (query : string)
    (knowledge_items : knowledge_item list option)
    : reasoning_chain =
  
  let analysis = analyze_query query in
  let rtype = analysis.reasoning_type in
  
  (* Decompose query into steps *)
  let steps = match rtype with
    | Causal -> decompose_causal_query query
    | Logical -> decompose_logical_query query
    | Mathematical -> decompose_mathematical_query query
    | Comparative -> decompose_comparative_query query
    | Analytical -> decompose_analytical_query query
    | _ -> decompose_general_query query
  in
  
  (* Generate reasoning for each step *)
  let rec process_steps acc remaining idx =
    match remaining with
    | [] -> List.rev acc
    | step :: rest ->
        let previous = List.rev acc in
        
        (* Get knowledge for this step *)
        let step_knowledge = match knowledge_items with
          | Some items -> items
          | None -> []
        in
        
        (* Generate reasoning *)
        let reasoning = generate_step_reasoning query step previous step_knowledge in
        
        (* Assess confidence *)
        let confidence = assess_step_confidence step step_knowledge in
        
        (* Update step *)
        let updated_step = {
          step with
          reasoning;
          confidence;
          knowledge_used = step_knowledge;
        } in
        
        process_steps (updated_step :: acc) rest (idx + 1)
  in
  
  let steps_with_reasoning = process_steps [] steps 1 in
  
  (* Synthesize conclusion *)
  let conclusion = synthesize_conclusion steps_with_reasoning query rtype in
  
  (* Calculate overall confidence *)
  let avg_confidence = 
    let confidences = List.map (fun step -> step.confidence) steps_with_reasoning in
    average_float confidences
  in
  
  (* Verify reasoning chain *)
  let verification_result = verify_reasoning_chain steps_with_reasoning conclusion in
  
  (* Calculate quality score *)
  let quality_score = 
    calculate_reasoning_quality steps_with_reasoning conclusion verification_result
  in
  
  (* Extract topics involved *)
  let topics_involved = analysis.topics in
  
  (* Detect relationships (simplified) *)
  let relationships = [] in (* Would be populated from knowledge synthesis *)
  
  {
    query;
    reasoning_type = rtype;
    steps = steps_with_reasoning;
    conclusion;
    confidence = avg_confidence;
    verification_result;
    quality_score;
    topics_involved;
    relationships;
  }

(******************************************************************************)
(* Formatting Functions *)
(******************************************************************************)

let format_reasoning_type (rtype : reasoning_type) : string =
  match rtype with
  | Causal -> "Causal"
  | Logical -> "Logical"
  | Mathematical -> "Mathematical"
  | Comparative -> "Comparative"
  | Analytical -> "Analytical"
  | Temporal -> "Temporal"
  | Spatial -> "Spatial"
  | Inductive -> "Inductive"
  | Deductive -> "Deductive"
  | Abductive -> "Abductive"
  | General -> "General"

let format_domain (dom : domain) : string =
  match dom with
  | Science -> "Science"
  | Economics -> "Economics"
  | Technology -> "Technology"
  | Environment -> "Environment"
  | Politics -> "Politics"
  | Health -> "Health"
  | Education -> "Education"
  | History -> "History"
  | Philosophy -> "Philosophy"
  | GeneralDomain -> "General"

let format_relationship_type (rel_type : relationship_type) : string =
  match rel_type with
  | CausalRel -> "causal"
  | HierarchicalRel -> "hierarchical"
  | AssociativeRel -> "associative"
  | ComparativeRel -> "comparative"
  | TemporalRel -> "temporal"
  | SpatialRel -> "spatial"

let format_reasoning_output (chain : reasoning_chain) : string =
  let header = 
    Printf.sprintf "Reasoning Chain Analysis\n=======================\nQuery: %s\nReasoning Type: %s\n"
      chain.query (format_reasoning_type chain.reasoning_type)
  in
  
  let step_strings = 
    List.map (fun step ->
      let evidence_str = 
        if List.length step.evidence > 0 then
          "\nEvidence: " ^ String.concat "; " step.evidence
        else ""
      in
      let knowledge_str = 
        if List.length step.knowledge_used > 0 then
          Printf.sprintf "\nKnowledge Items Used: %d" (List.length step.knowledge_used)
        else ""
      in
      Printf.sprintf "Step %d: %s\nReasoning: %s\nConfidence: %.2f%s%s"
        step.step_number step.description step.reasoning step.confidence 
        evidence_str knowledge_str
    ) chain.steps
  in
  
  let steps_section = String.concat "\n\n" step_strings in
  
  let conclusion_section = 
    Printf.sprintf "\n\nConclusion: %s" chain.conclusion
  in
  
  let metrics_section = 
    Printf.sprintf 
      "\n\nMetrics:\n- Overall Confidence: %.2f\n- Quality Score: %.2f\n- Verification: %s\n- Topics Involved: %s"
      chain.confidence chain.quality_score
      (if chain.verification_result then "Passed" else "Failed")
      (String.concat ", " chain.topics_involved)
  in
  
  let relationships_section = 
    if List.length chain.relationships > 0 then
      let rel_strings = List.map (fun rel ->
        Printf.sprintf "  - %s %s %s (strength: %.2f)"
          rel.topic1 (format_relationship_type rel.rel_type) rel.topic2 rel.strength
      ) chain.relationships in
      "\n\nRelationships:\n" ^ String.concat "\n" rel_strings
    else
      ""
  in
  
  header ^ steps_section ^ conclusion_section ^ metrics_section ^ relationships_section

(******************************************************************************)
(* Multi-Topic Reasoning Support *)
(******************************************************************************)

let detect_multi_topic_query (query : string) : bool =
  let analysis = analyze_query query in
  analysis.requires_multi_topic

let extract_multi_topic_knowledge 
    (query : string)
    (topics : topic_info list)
    : (string * knowledge_item list) list =
  
  List.map (fun topic_info ->
    (topic_info.topic_name, topic_info.knowledge_items)
  ) topics

let generate_multi_topic_reasoning_chain 
    (query : string)
    (knowledge_by_topic : (string * knowledge_item list) list)
    : reasoning_chain =
  
  (* Synthesize knowledge from multiple topics *)
  let synthesis = synthesize_knowledge knowledge_by_topic query None in
  
  (* Flatten knowledge items *)
  let all_knowledge = 
    List.fold_left (fun acc (_, items) -> items @ acc) [] knowledge_by_topic
  in
  
  (* Generate reasoning chain with synthesized knowledge *)
  let chain = generate_reasoning_chain query (Some all_knowledge) in
  
  (* Update with relationships from synthesis *)
  {
    chain with
    relationships = synthesis.relationships;
    topics_involved = synthesis.topics_covered;
  }

(******************************************************************************)
(* Causal Chain Reasoning *)
(******************************************************************************)

let generate_causal_chain 
    (query : string)
    (cause_topic : string)
    (effect_topic : string)
    (knowledge_items : knowledge_item list)
    : reasoning_chain =
  
  (* Create specialized causal steps *)
  let causal_steps = [
    { step_number = 1; 
      description = Printf.sprintf "Analyze '%s' as the cause" cause_topic;
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = []; knowledge_used = [] };
    { step_number = 2; 
      description = Printf.sprintf "Analyze '%s' as the effect" effect_topic;
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [1]; knowledge_used = [] };
    { step_number = 3; 
      description = "Identify the causal mechanism";
      reasoning = ""; confidence = 0.8; evidence = []; sub_steps = []; 
      dependencies = [1; 2]; knowledge_used = [] };
    { step_number = 4; 
      description = "Evaluate the strength of the causal link";
      reasoning = ""; confidence = 0.7; evidence = []; sub_steps = []; 
      dependencies = [3]; knowledge_used = [] };
  ] in
  
  (* Process steps *)
  let rec process_causal_steps acc remaining idx =
    match remaining with
    | [] -> List.rev acc
    | step :: rest ->
        let previous = List.rev acc in
        let reasoning = generate_step_reasoning query step previous knowledge_items in
        let confidence = assess_step_confidence step knowledge_items in
        let updated_step = {
          step with
          reasoning;
          confidence;
          knowledge_used = knowledge_items;
        } in
        process_causal_steps (updated_step :: acc) rest (idx + 1)
  in
  
  let steps_with_reasoning = process_causal_steps [] causal_steps 1 in
  
  (* Synthesize causal conclusion *)
  let conclusion = 
    Printf.sprintf 
      "The causal relationship between '%s' and '%s' is established through: %s"
      cause_topic effect_topic
      (String.concat ". " (List.map (fun s -> s.reasoning) steps_with_reasoning))
  in
  
  let avg_confidence = 
    let confidences = List.map (fun step -> step.confidence) steps_with_reasoning in
    average_float confidences
  in
  
  {
    query;
    reasoning_type = Causal;
    steps = steps_with_reasoning;
    conclusion;
    confidence = avg_confidence;
    verification_result = verify_reasoning_chain steps_with_reasoning conclusion;
    quality_score = calculate_reasoning_quality steps_with_reasoning conclusion true;
    topics_involved = [cause_topic; effect_topic];
    relationships = [
      {
        topic1 = cause_topic;
        topic2 = effect_topic;
        rel_type = CausalRel;
        strength = avg_confidence;
        confidence = avg_confidence;
        evidence = conclusion;
      }
    ];
  }

(******************************************************************************)
(* Statistics and Metrics *)
(******************************************************************************)

type reasoning_stats = {
  total_queries : int;
  avg_confidence : float;
  avg_quality_score : float;
  verification_rate : float;
  reasoning_type_distribution : (reasoning_type * int) list;
  avg_steps_per_chain : float;
}

let calculate_stats (chains : reasoning_chain list) : reasoning_stats =
  let total = List.length chains in
  if total = 0 then
    {
      total_queries = 0;
      avg_confidence = 0.0;
      avg_quality_score = 0.0;
      verification_rate = 0.0;
      reasoning_type_distribution = [];
      avg_steps_per_chain = 0.0;
    }
  else (
    let confidences = List.map (fun c -> c.confidence) chains in
    let quality_scores = List.map (fun c -> c.quality_score) chains in
    let verified_count = 
      List.fold_left (fun acc c -> if c.verification_result then acc + 1 else acc) 0 chains
    in
    let step_counts = List.map (fun c -> List.length c.steps) chains in
    
    (* Count reasoning types *)
    let type_counts = ref [] in
    List.iter (fun chain ->
      let existing = list_assoc_opt chain.reasoning_type !type_counts in
      match existing with
      | Some count -> 
          type_counts := 
            (chain.reasoning_type, count + 1) :: 
            (list_remove_assoc chain.reasoning_type !type_counts)
      | None -> 
          type_counts := (chain.reasoning_type, 1) :: !type_counts
    ) chains;
    
    {
      total_queries = total;
      avg_confidence = average_float confidences;
      avg_quality_score = average_float quality_scores;
      verification_rate = float_of_int verified_count /. float_of_int total;
      reasoning_type_distribution = !type_counts;
      avg_steps_per_chain = average_float (List.map float_of_int step_counts);
    }
  )

let format_stats (stats : reasoning_stats) : string =
  Printf.sprintf 
    "Reasoning Statistics\n====================\n\
     Total Queries: %d\n\
     Average Confidence: %.2f\n\
     Average Quality Score: %.2f\n\
     Verification Rate: %.2f%%\n\
     Average Steps per Chain: %.2f\n\
     Reasoning Type Distribution:\n%s"
    stats.total_queries
    stats.avg_confidence
    stats.avg_quality_score
    (stats.verification_rate *. 100.0)
    stats.avg_steps_per_chain
    (String.concat "\n" 
       (List.map (fun (rtype, count) ->
          Printf.sprintf "  - %s: %d" (format_reasoning_type rtype) count
        ) stats.reasoning_type_distribution))

(******************************************************************************)
(* Error Handling *)
(******************************************************************************)

type reasoning_error =
  | InvalidQuery of string
  | InsufficientKnowledge of string
  | VerificationFailed of string
  | InvalidStepDependencies of string

let handle_reasoning_error (error : reasoning_error) : string =
  match error with
  | InvalidQuery msg -> Printf.sprintf "Invalid query: %s" msg
  | InsufficientKnowledge msg -> Printf.sprintf "Insufficient knowledge: %s" msg
  | VerificationFailed msg -> Printf.sprintf "Verification failed: %s" msg
  | InvalidStepDependencies msg -> Printf.sprintf "Invalid step dependencies: %s" msg

(******************************************************************************)
(* Main Entry Point *)
(******************************************************************************)

let reason_about_query (query : string) : reasoning_chain =
  (* Validate query *)
  if String.length query = 0 then
    failwith "Empty query provided"
  else if String.length query > 1000 then
    failwith "Query too long"
  else
    generate_reasoning_chain query None

let reason_about_query_with_knowledge 
    (query : string) 
    (knowledge_items : knowledge_item list) 
    : reasoning_chain =
  
  generate_reasoning_chain query (Some knowledge_items)

let reason_about_multi_topic_query 
    (query : string)
    (knowledge_by_topic : (string * knowledge_item list) list)
    : reasoning_chain =
  
  generate_multi_topic_reasoning_chain query knowledge_by_topic

(******************************************************************************)
(* Example Usage Functions *)
(******************************************************************************)

let example_causal_query () : reasoning_chain =
  reason_about_query "How does climate change affect economic policy?"

let example_comparative_query () : reasoning_chain =
  reason_about_query "Compare quantum computing to classical computing"

let example_analytical_query () : reasoning_chain =
  reason_about_query "Analyze the relationship between neural networks and biological neurons"

let example_with_knowledge () : reasoning_chain =
  let knowledge = [
    {
      topic = "climate change";
      title = "Climate Change Overview";
      content = "Climate change refers to long-term shifts in global temperatures and weather patterns.";
      source = "wikipedia";
      confidence = 0.9;
      domain = Environment;
    };
    {
      topic = "economic policy";
      title = "Economic Policy Basics";
      content = "Economic policy refers to government actions that influence economic activity.";
      source = "wikipedia";
      confidence = 0.9;
      domain = Economics;
    };
  ] in
  reason_about_query_with_knowledge 
    "How does climate change affect economic policy?" 
    knowledge

(******************************************************************************)
(* Advanced Query Processing *)
(******************************************************************************)

(** Extract entities from query *)
let extract_entities (query : string) : string list =
  let words = extract_meaningful_words (String.lowercase_ascii query) 4 in
  let stop_words = ["what", "how", "why", "when", "where", "which", "who",
                   "does", "do", "is", "are", "the", "a", "an", "and", "or",
                   "does", "affect", "impact", "influence", "compare", "analyze"] in
  List.filter (fun w -> not (List.mem w stop_words)) words

(** Detect query complexity level *)
let detect_complexity_level (query : string) : int =
  let analysis = analyze_query query in
  let word_count = List.length (split_words query) in
  let question_count = count_word_occurrences query "?" in
  let conjunction_count = 
    (count_word_occurrences query "and") +
    (count_word_occurrences query "or") +
    (count_word_occurrences query "but")
  in
  
  let base_score = 
    if analysis.complexity > 0.8 then 3
    else if analysis.complexity > 0.6 then 2
    else 1
  in
  
  let word_score = 
    if word_count > 20 then 2
    else if word_count > 10 then 1
    else 0
  in
  
  let structure_score = 
    if question_count > 1 || conjunction_count > 2 then 1 else 0
  in
  
  min (base_score + word_score + structure_score) 5

(** Extract key phrases from query *)
let extract_key_phrases (query : string) : string list =
  let query_lower = String.lowercase_ascii query in
  let phrases = ref [] in
  
  (* Common phrase patterns *)
  let patterns = [
    ("how does", "how does");
    ("how do", "how do");
    ("why does", "why does");
    ("what causes", "what causes");
    ("what is", "what is");
    ("what are", "what are");
    ("compare", "compare");
    ("difference between", "difference between");
    ("relationship between", "relationship between");
    ("effect of", "effect of");
    ("impact of", "impact of");
  ] in
  
  List.iter (fun (pattern, phrase) ->
    if contains_substring query_lower pattern then
      phrases := phrase :: !phrases
  ) patterns;
  
  !phrases

(******************************************************************************)
(* Knowledge Filtering and Ranking *)
(******************************************************************************)

(** Filter knowledge by relevance *)
let filter_knowledge_by_relevance 
    (knowledge_items : knowledge_item list)
    (query : string)
    (min_relevance : float)
    : knowledge_item list =
  
  let query_words = extract_meaningful_words (String.lowercase_ascii query) 3 in
  
  let calculate_relevance (item : knowledge_item) : float =
    let content_lower = String.lowercase_ascii item.content in
    let title_lower = String.lowercase_ascii item.title in
    
    (* Title match bonus *)
    let title_score = 
      if contains_substring title_lower query then 0.3 else 0.0
    in
    
    (* Content word overlap *)
    let content_words = extract_meaningful_words content_lower 3 in
    let overlap = 
      List.fold_left (fun acc word ->
        if List.mem word content_words then acc + 1 else acc
      ) 0 query_words
    in
    let content_score = 
      if List.length query_words > 0 then
        float_of_int overlap /. float_of_int (List.length query_words) *. 0.5
      else 0.0
    in
    
    (* Confidence factor *)
    let confidence_factor = item.confidence *. 0.2 in
    
    normalize_confidence (title_score +. content_score +. confidence_factor)
  in
  
  let scored_items = 
    List.map (fun item -> (item, calculate_relevance item)) knowledge_items
  in
  
  let filtered = 
    List.filter (fun (_, score) -> score >= min_relevance) scored_items
  in
  
  (* Sort by relevance *)
  let sorted = 
    List.sort (fun (_, s1) (_, s2) -> compare s2 s1) filtered
  in
  
  List.map fst sorted

(** Rank knowledge items by quality *)
let rank_knowledge_by_quality 
    (knowledge_items : knowledge_item list)
    : knowledge_item list =
  
  let calculate_quality_score (item : knowledge_item) : float =
    let length_score = 
      let len = String.length item.content in
      if len >= 100 && len <= 1000 then 0.3
      else if len > 100 then 0.2
      else 0.1
    in
    
    let confidence_score = item.confidence *. 0.4 in
    
    let source_score = 
      match item.source with
      | "wikipedia" -> 0.2
      | "structured" -> 0.15
      | _ -> 0.1
    in
    
    let domain_score = 
      if item.domain <> GeneralDomain then 0.1 else 0.0
    in
    
    normalize_confidence (length_score +. confidence_score +. source_score +. domain_score)
  in
  
  let scored_items = 
    List.map (fun item -> (item, calculate_quality_score item)) knowledge_items
  in
  
  let sorted = 
    List.sort (fun (_, s1) (_, s2) -> compare s2 s1) scored_items
  in
  
  List.map fst sorted

(******************************************************************************)
(* Step Dependency Resolution *)
(******************************************************************************)

(** Resolve step dependencies *)
let resolve_dependencies (steps : reasoning_step list) : reasoning_step list =
  let step_map = 
    List.fold_left (fun acc step ->
      (step.step_number, step) :: acc
    ) [] steps
  in
  
  let get_step (num : int) : reasoning_step option =
    try Some (List.assoc num step_map)
    with Not_found -> None
  in
  
  let verify_dependencies (step : reasoning_step) : bool =
    List.for_all (fun dep_num ->
      match get_step dep_num with
      | Some dep_step -> dep_step.step_number < step.step_number
      | None -> false
    ) step.dependencies
  in
  
  List.filter verify_dependencies steps

(** Topological sort of steps by dependencies *)
let topological_sort_steps (steps : reasoning_step list) : reasoning_step list =
  let rec visit (step : reasoning_step) (visited : int list ref) 
                (result : reasoning_step list ref) =
    if List.mem step.step_number !visited then ()
    else (
      (* Visit dependencies first *)
      List.iter (fun dep_num ->
        let dep_step = List.find (fun s -> s.step_number = dep_num) steps in
        visit dep_step visited result
      ) step.dependencies;
      
      visited := step.step_number :: !visited;
      result := step :: !result
    )
  in
  
  let visited = ref [] in
  let result = ref [] in
  
  List.iter (fun step -> visit step visited result) steps;
  
  List.rev !result

(******************************************************************************)
(* Evidence Collection *)
(******************************************************************************)

(** Collect evidence from knowledge items *)
let collect_evidence 
    (knowledge_items : knowledge_item list)
    (query : string)
    : string list =
  
  let query_lower = String.lowercase_ascii query in
  let query_words = extract_meaningful_words query_lower 3 in
  
  let extract_evidence (item : knowledge_item) : string list =
    let content_words = extract_meaningful_words 
                          (String.lowercase_ascii item.content) 3 in
    
    (* Find sentences that contain query words *)
    let sentences = 
      let rec split_sentences acc current i =
        if i >= String.length item.content then
          if current <> "" then current :: acc else acc
        else
          let c = item.content.[i] in
          if c = '.' || c = '!' || c = '?' then
            split_sentences (current :: acc) "" (i + 1)
          else
            split_sentences acc (current ^ String.make 1 c) (i + 1)
      in
      split_sentences [] "" 0
    in
    
    List.filter (fun sentence ->
      let sentence_lower = String.lowercase_ascii sentence in
      List.exists (fun word -> contains_substring sentence_lower word) query_words
    ) sentences
  in
  
  let all_evidence = 
    List.fold_left (fun acc item -> extract_evidence item @ acc) [] knowledge_items
  in
  
  (* Remove duplicates and limit *)
  let unique_evidence = 
    List.sort_uniq compare all_evidence
  in
  
  list_take 10 unique_evidence

(** Score evidence relevance *)
let score_evidence_relevance (evidence : string) (query : string) : float =
  let evidence_lower = String.lowercase_ascii evidence in
  let query_lower = String.lowercase_ascii query in
  let query_words = extract_meaningful_words query_lower 3 in
  
  let word_matches = 
    List.fold_left (fun acc word ->
      if contains_substring evidence_lower word then acc + 1 else acc
    ) 0 query_words
  in
  
  if List.length query_words = 0 then 0.0
  else float_of_int word_matches /. float_of_int (List.length query_words)

(******************************************************************************)
(* Advanced Reasoning Strategies *)
(******************************************************************************)

(** Generate alternative reasoning paths *)
let generate_alternative_paths 
    (query : string)
    (main_chain : reasoning_chain)
    : reasoning_chain list =
  
  (* Generate alternative by changing reasoning type *)
  let alternative_types = match main_chain.reasoning_type with
    | Causal -> [Analytical; Comparative]
    | Comparative -> [Analytical; Causal]
    | Analytical -> [Causal; Comparative]
    | _ -> [Causal; Analytical; Comparative]
  in
  
  List.map (fun alt_type ->
    let alt_steps = match alt_type with
      | Causal -> decompose_causal_query query
      | Comparative -> decompose_comparative_query query
      | Analytical -> decompose_analytical_query query
      | _ -> decompose_general_query query
    in
    
    (* Process steps *)
    let rec process_alt_steps acc remaining idx =
      match remaining with
      | [] -> List.rev acc
      | step :: rest ->
          let previous = List.rev acc in
          let reasoning = generate_step_reasoning query step previous [] in
          let confidence = assess_step_confidence step [] in
          let updated_step = {
            step with
            reasoning;
            confidence;
          } in
          process_alt_steps (updated_step :: acc) rest (idx + 1)
    in
    
    let steps_with_reasoning = process_alt_steps [] alt_steps 1 in
    let conclusion = synthesize_conclusion steps_with_reasoning query alt_type in
    let avg_confidence = 
      let confidences = List.map (fun s -> s.confidence) steps_with_reasoning in
      average_float confidences
    in
    
    {
      query;
      reasoning_type = alt_type;
      steps = steps_with_reasoning;
      conclusion;
      confidence = avg_confidence;
      verification_result = verify_reasoning_chain steps_with_reasoning conclusion;
      quality_score = calculate_reasoning_quality steps_with_reasoning conclusion true;
      topics_involved = main_chain.topics_involved;
      relationships = [];
    }
  ) alternative_types

(** Merge multiple reasoning chains *)
let merge_reasoning_chains 
    (chains : reasoning_chain list)
    : reasoning_chain option =
  
  if List.length chains = 0 then None
  else (
    let first_chain = List.hd chains in
    
    (* Combine all steps *)
    let all_steps = 
      List.fold_left (fun acc chain -> chain.steps @ acc) [] chains
    in
    
    (* Remove duplicate steps *)
    let unique_steps = 
      let rec remove_duplicates acc remaining =
        match remaining with
        | [] -> List.rev acc
        | step :: rest ->
            if List.exists (fun s -> s.description = step.description) acc then
              remove_duplicates acc rest
            else
              remove_duplicates (step :: acc) rest
      in
      remove_duplicates [] all_steps
    in
    
    (* Renumber steps *)
    let renumbered_steps = 
      List.mapi (fun i step ->
        { step with step_number = i + 1 }
      ) unique_steps
    in
    
    (* Combine conclusions *)
    let combined_conclusion = 
      String.concat " " (List.map (fun c -> c.conclusion) chains)
    in
    
    (* Calculate average metrics *)
    let avg_confidence = 
      let confidences = List.map (fun c -> c.confidence) chains in
      average_float confidences
    in
    
    let avg_quality = 
      let qualities = List.map (fun c -> c.quality_score) chains in
      average_float qualities
    in
    
    (* Combine topics *)
    let all_topics = 
      List.fold_left (fun acc chain -> chain.topics_involved @ acc) [] chains
    in
    let unique_topics = 
      let rec remove_dups acc remaining =
        match remaining with
        | [] -> List.rev acc
        | topic :: rest ->
            if List.mem topic acc then remove_dups acc rest
            else remove_dups (topic :: acc) rest
      in
      remove_dups [] all_topics
    in
    
    (* Combine relationships *)
    let all_relationships = 
      List.fold_left (fun acc chain -> chain.relationships @ acc) [] chains
    in
    
    Some {
      query = first_chain.query;
      reasoning_type = first_chain.reasoning_type;
      steps = renumbered_steps;
      conclusion = combined_conclusion;
      confidence = avg_confidence;
      verification_result = List.for_all (fun c -> c.verification_result) chains;
      quality_score = avg_quality;
      topics_involved = unique_topics;
      relationships = all_relationships;
    }
  )

(******************************************************************************)
(* Query Expansion *)
(******************************************************************************)

(** Expand query with synonyms and related terms *)
let expand_query (query : string) : string list =
  let query_lower = String.lowercase_ascii query in
  let expansions = ref [query] in
  
  (* Simple synonym expansion *)
  let synonyms = [
    ("affect", ["impact"; "influence"; "change"]);
    ("cause", ["lead to"; "result in"; "bring about"]);
    ("compare", ["contrast"; "examine differences"; "evaluate"]);
    ("analyze", ["examine"; "study"; "investigate"]);
    ("explain", ["describe"; "clarify"; "elucidate"]);
  ] in
  
  List.iter (fun (word, syns) ->
    if contains_substring query_lower word then
      List.iter (fun syn ->
        let expanded = 
          global_replace (regexp_string word) syn query_lower
        in
        if not (List.mem expanded !expansions) then
          expansions := expanded :: !expansions
      ) syns
  ) synonyms;
  
  !expansions

(** Generate query variations *)
let generate_query_variations (query : string) : string list =
  let variations = ref [query] in
  
  (* Add question mark if missing *)
  if not (String.contains query '?') then
    variations := (query ^ "?") :: !variations;
  
  (* Generate "what is" variation *)
  if not (contains_substring (String.lowercase_ascii query) "what is") then
    variations := ("What is " ^ query) :: !variations;
  
  (* Generate "how does" variation *)
  if not (contains_substring (String.lowercase_ascii query) "how") then
    variations := ("How does " ^ query ^ " work?") :: !variations;
  
  !variations

(******************************************************************************)
(* Confidence Calibration *)
(******************************************************************************)

(** Calibrate confidence scores based on evidence *)
let calibrate_confidence 
    (base_confidence : float)
    (evidence_count : int)
    (knowledge_count : int)
    (verification_passed : bool)
    : float =
  
  let evidence_bonus = 
    min (float_of_int evidence_count *. 0.05) 0.2
  in
  
  let knowledge_bonus = 
    if knowledge_count >= 3 then 0.15
    else if knowledge_count >= 1 then 0.1
    else 0.0
  in
  
  let verification_bonus = 
    if verification_passed then 0.1 else 0.0
  in
  
  normalize_confidence 
    (base_confidence +. evidence_bonus +. knowledge_bonus +. verification_bonus)

(** Adjust confidence based on step dependencies *)
let adjust_confidence_by_dependencies 
    (step : reasoning_step)
    (dependency_steps : reasoning_step list)
    : float =
  
  let base_confidence = step.confidence in
  
  (* Reduce confidence if dependencies have low confidence *)
  let dependency_confidence = 
    if List.length dependency_steps > 0 then
      let confidences = List.map (fun s -> s.confidence) dependency_steps in
      average_float confidences
    else 1.0
  in
  
  (* Penalize if dependencies failed *)
  let dependency_penalty = 
    if dependency_confidence < 0.6 then 0.1 else 0.0
  in
  
  normalize_confidence (base_confidence *. dependency_confidence -. dependency_penalty)

(******************************************************************************)
(* Step Validation *)
(******************************************************************************)

(** Validate reasoning step *)
let validate_step (step : reasoning_step) : bool * string list =
  let errors = ref [] in
  
  (* Check step number *)
  if step.step_number <= 0 then
    errors := "Invalid step number" :: !errors;
  
  (* Check description *)
  if String.length step.description = 0 then
    errors := "Empty step description" :: !errors;
  
  (* Check confidence range *)
  if step.confidence < 0.0 || step.confidence > 1.0 then
    errors := "Confidence out of range" :: !errors;
  
  (* Check dependencies *)
  List.iter (fun dep ->
    if dep >= step.step_number then
      errors := Printf.sprintf "Invalid dependency: step %d depends on step %d" 
                                step.step_number dep :: !errors
  ) step.dependencies;
  
  (List.length !errors = 0, !errors)

(** Validate reasoning chain *)
let validate_reasoning_chain (chain : reasoning_chain) : bool * string list =
  let errors = ref [] in
  
  (* Check query *)
  if String.length chain.query = 0 then
    errors := "Empty query" :: !errors;
  
  (* Check steps *)
  if List.length chain.steps = 0 then
    errors := "No reasoning steps" :: !errors;
  
  (* Validate each step *)
  List.iter (fun step ->
    let (valid, step_errors) = validate_step step in
    if not valid then
      errors := step_errors @ !errors
  ) chain.steps;
  
  (* Check conclusion *)
  if String.length chain.conclusion = 0 then
    errors := "Empty conclusion" :: !errors;
  
  (* Check confidence *)
  if chain.confidence < 0.0 || chain.confidence > 1.0 then
    errors := "Confidence out of range" :: !errors;
  
  (* Check step numbering *)
  let step_numbers = List.map (fun s -> s.step_number) chain.steps in
  let sorted_numbers = List.sort compare step_numbers in
  let expected = 
    List.init (List.length chain.steps) (fun i -> i + 1)
  in
  if step_numbers <> expected then
    errors := "Step numbers not sequential" :: !errors;
  
  (List.length !errors = 0, !errors)

(******************************************************************************)
(* Performance Metrics *)
(******************************************************************************)

type performance_metrics = {
  total_processing_time : float;
  avg_time_per_step : float;
  max_steps_in_chain : int;
  min_steps_in_chain : int;
  avg_knowledge_items_per_query : float;
  cache_hit_rate : float;
}

let calculate_performance_metrics 
    (chains : reasoning_chain list)
    (processing_times : float list)
    : performance_metrics =
  
  let total_time = 
    List.fold_left (fun acc t -> acc +. t) 0.0 processing_times
  in
  
  let avg_time = 
    if List.length processing_times > 0 then
      total_time /. float_of_int (List.length processing_times)
    else 0.0
  in
  
  let step_counts = List.map (fun c -> List.length c.steps) chains in
  
  let max_steps = 
    if List.length step_counts > 0 then
      List.fold_left max 0 step_counts
    else 0
  in
  
  let min_steps = 
    if List.length step_counts > 0 then
      List.fold_left min max_int step_counts
    else 0
  in
  
  {
    total_processing_time = total_time;
    avg_time_per_step = avg_time;
    max_steps_in_chain = max_steps;
    min_steps_in_chain = min_steps;
    avg_knowledge_items_per_query = 0.0; (* Would need knowledge tracking *)
    cache_hit_rate = 0.0; (* Would need cache implementation *)
  }

(******************************************************************************)
(* Advanced Formatting *)
(******************************************************************************)

(** Format reasoning chain as JSON-like structure *)
let format_reasoning_json (chain : reasoning_chain) : string =
  let format_step_json (step : reasoning_step) : string =
    Printf.sprintf 
      "{\"step_number\": %d, \"description\": \"%s\", \"reasoning\": \"%s\", \"confidence\": %.2f}"
      step.step_number step.description step.reasoning step.confidence
  in
  
  let steps_json = 
    String.concat ", " (List.map format_step_json chain.steps)
  in
  
  Printf.sprintf 
    "{\"query\": \"%s\", \"reasoning_type\": \"%s\", \"steps\": [%s], \"conclusion\": \"%s\", \"confidence\": %.2f}"
    chain.query (format_reasoning_type chain.reasoning_type) steps_json 
    chain.conclusion chain.confidence

(** Format reasoning chain as markdown *)
let format_reasoning_markdown (chain : reasoning_chain) : string =
  let header = Printf.sprintf "# Reasoning Analysis\n\n**Query:** %s\n\n" chain.query in
  
  let reasoning_type_section = 
    Printf.sprintf "**Reasoning Type:** %s\n\n" (format_reasoning_type chain.reasoning_type)
  in
  
  let steps_section = 
    let step_strings = List.map (fun step ->
      Printf.sprintf "## Step %d: %s\n\n%s\n\n*Confidence: %.2f*\n"
        step.step_number step.description step.reasoning step.confidence
    ) chain.steps in
    "## Reasoning Steps\n\n" ^ String.concat "\n" step_strings
  in
  
  let conclusion_section = 
    Printf.sprintf "## Conclusion\n\n%s\n\n" chain.conclusion
  in
  
  let metrics_section = 
    Printf.sprintf 
      "## Metrics\n\n- **Confidence:** %.2f\n- **Quality Score:** %.2f\n- **Verification:** %s\n"
      chain.confidence chain.quality_score
      (if chain.verification_result then "✓ Passed" else "✗ Failed")
  in
  
  header ^ reasoning_type_section ^ steps_section ^ conclusion_section ^ metrics_section

(** Format reasoning chain as HTML *)
let format_reasoning_html (chain : reasoning_chain) : string =
  let html_header = 
    "<!DOCTYPE html>\n<html>\n<head><title>Reasoning Analysis</title></head>\n<body>\n"
  in
  
  let html_title = Printf.sprintf "<h1>Reasoning Analysis</h1>\n<p><strong>Query:</strong> %s</p>\n" chain.query in
  
  let html_steps = 
    let step_html = List.map (fun step ->
      Printf.sprintf 
        "<div class=\"step\">\n<h2>Step %d: %s</h2>\n<p>%s</p>\n<p><em>Confidence: %.2f</em></p>\n</div>\n"
        step.step_number step.description step.reasoning step.confidence
    ) chain.steps in
    "<h2>Reasoning Steps</h2>\n" ^ String.concat "\n" step_html
  in
  
  let html_conclusion = 
    Printf.sprintf "<h2>Conclusion</h2>\n<p>%s</p>\n" chain.conclusion
  in
  
  let html_footer = "</body>\n</html>\n" in
  
  html_header ^ html_title ^ html_steps ^ html_conclusion ^ html_footer

(******************************************************************************)
(* Caching Support *)
(******************************************************************************)

type cache_entry = {
  query_hash : string;
  query : string;
  chain : reasoning_chain;
  timestamp : float;
}

let cache : (string, cache_entry) Hashtbl.t = Hashtbl.create 100

(** Hash query for caching *)
let hash_query (query : string) : string =
  let rec hash_string s i acc =
    if i >= String.length s then acc
    else hash_string s (i + 1) ((acc * 31 + int_of_char s.[i]) mod 1000000007)
  in
  string_of_int (hash_string query 0 0)

(** Check cache for existing reasoning *)
let check_cache (query : string) : reasoning_chain option =
  let query_hash = hash_query query in
  try
    let entry = Hashtbl.find cache query_hash in
    (* Check if cache entry is still valid (e.g., less than 1 hour old) *)
    let current_time = time () in
    if current_time -. entry.timestamp < 3600.0 then
      Some entry.chain
    else (
      Hashtbl.remove cache query_hash;
      None
    )
  with Not_found -> None

(** Store reasoning in cache *)
let store_in_cache (query : string) (chain : reasoning_chain) : unit =
  let query_hash = hash_query query in
  let entry = {
    query_hash;
    query;
    chain;
    timestamp = time ();
  } in
  Hashtbl.replace cache query_hash entry

(** Clear cache *)
let clear_cache () : unit =
  Hashtbl.clear cache

(** Get cache statistics *)
let get_cache_stats () : int * int =
  (Hashtbl.length cache, Hashtbl.length cache)

(******************************************************************************)
(* Batch Processing *)
(******************************************************************************)

(** Process multiple queries in batch *)
let process_batch_queries (queries : string list) : reasoning_chain list =
  List.map reason_about_query queries

(** Process queries with shared knowledge *)
let process_batch_with_knowledge 
    (queries : string list)
    (shared_knowledge : knowledge_item list)
    : reasoning_chain list =
  
  List.map (fun query ->
    reason_about_query_with_knowledge query shared_knowledge
  ) queries

(** Parallel processing simulation *)
let process_parallel (queries : string list) (workers : int) : reasoning_chain list =
  (* Simple round-robin distribution *)
  let rec distribute queries worker_idx acc =
    match queries with
    | [] -> List.rev acc
    | query :: rest ->
        let chain = reason_about_query query in
        distribute rest ((worker_idx + 1) mod workers) (chain :: acc)
  in
  distribute queries 0 []

(******************************************************************************)
(* Export Functions *)
(******************************************************************************)

(** Export reasoning chain to string representation *)
let export_reasoning_chain (chain : reasoning_chain) : string =
  format_reasoning_output chain

(** Import reasoning chain from string (simplified) *)
let import_reasoning_chain (data : string) : reasoning_chain option =
  (* Simplified import - would need proper parsing in real implementation *)
  None

(** Serialize reasoning chain *)
let serialize_chain (chain : reasoning_chain) : string =
  format_reasoning_json chain

(** Deserialize reasoning chain *)
let deserialize_chain (data : string) : reasoning_chain option =
  (* Simplified deserialization - would need proper JSON parsing *)
  None

(******************************************************************************)
(* Testing and Validation Helpers *)
(******************************************************************************)

(** Create test reasoning chain *)
let create_test_chain () : reasoning_chain =
  reason_about_query "What is artificial intelligence?"

(** Run validation tests *)
let run_validation_tests () : bool =
  let test_chain = create_test_chain () in
  let (valid, errors) = validate_reasoning_chain test_chain in
  if not valid then
    List.iter print_endline errors;
  valid

(** Benchmark reasoning generation *)
let benchmark_reasoning (query : string) (iterations : int) : float =
  let start_time = gettimeofday () in
  for _ = 1 to iterations do
    ignore (reason_about_query query)
  done;
  let end_time = gettimeofday () in
  (end_time -. start_time) /. float_of_int iterations

(******************************************************************************)
(* Documentation and Examples *)
(******************************************************************************)

(** Example: Simple causal reasoning *)
let example_simple_causal () =
  let chain = reason_about_query "Why does it rain?" in
  format_reasoning_output chain

(** Example: Multi-topic reasoning *)
let example_multi_topic () =
  let knowledge = [
    ("climate", [
      {
        topic = "climate";
        title = "Climate Science";
        content = "Climate refers to long-term weather patterns.";
        source = "wikipedia";
        confidence = 0.9;
        domain = Science;
      }
    ]);
    ("economics", [
      {
        topic = "economics";
        title = "Economics Basics";
        content = "Economics studies how societies allocate resources.";
        source = "wikipedia";
        confidence = 0.9;
        domain = Economics;
      }
    ]);
  ] in
  let chain = reason_about_multi_topic_query 
                "How does climate change affect economics?" knowledge in
  format_reasoning_output chain

(** Example: Comparative reasoning *)
let example_comparative () =
  let chain = reason_about_query 
                "Compare machine learning to deep learning" in
  format_reasoning_output chain

(** Example: Analytical reasoning *)
let example_analytical () =
  let chain = reason_about_query 
                "Analyze the impact of social media on communication" in
  format_reasoning_output chain

(** Example: With evidence collection *)
let example_with_evidence () =
  let knowledge = [
    {
      topic = "neural networks";
      title = "Neural Networks";
      content = "Neural networks are computing systems inspired by biological neural networks.";
      source = "wikipedia";
      confidence = 0.9;
      domain = Technology;
    };
    {
      topic = "brain";
      title = "Human Brain";
      content = "The human brain processes information through interconnected neurons.";
      source = "wikipedia";
      confidence = 0.9;
      domain = Science;
    };
  ] in
  let chain = reason_about_query_with_knowledge 
                "How do neural networks relate to the human brain?" knowledge in
  format_reasoning_output chain

