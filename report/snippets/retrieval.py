    def retrieve(self, query, k=3, graph=True):
        q = normalize(query)
        if not q.strip():
            return []
        lexical = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        concepts = {n["id"] for n in self.graph["concepts"]
                    if any(re.search(r"(?<!\w)" + re.escape(normalize(a)) + r"(?!\w)", q)
                           for a in n["aliases"])}
        expanded = set(concepts)
        if graph:
            for edge in self.graph["relations"]:
                if edge["source"] in concepts:
                    expanded.add(edge["target"])
        results = []
        query_terms = set(re.findall(r"\w+", q)) - {"la", "gi", "va", "co", "khong", "toi", "can", "the", "nao", "cua", "cho"}
        for i, doc in enumerate(self.docs):
            matched = set(doc["concepts"]) & expanded
            bonus = .12 if graph and matched else 0.
            # Do not let graph proximity create evidence for an unrelated query.
            direct = bool(set(doc["concepts"]) & concepts)
            anchor_terms = set(re.findall(r"\w+", normalize(doc["title"] + " " + " ".join(doc["keywords"]))))
            if not direct and len(query_terms & anchor_terms) < 2:
                continue
            if lexical[i] < .10 and not direct:
                continue
            results.append({**doc, "score": float(lexical[i] + bonus),
                            "matched_concepts": sorted(matched), "lexical_score": float(lexical[i])})
        return sorted(results, key=lambda d: (-d["score"], d["id"]))[:k]
