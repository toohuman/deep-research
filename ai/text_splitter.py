#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import List, Optional

class TextSplitter(ABC):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Cannot have chunk_overlap >= chunk_size")

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """
        Abstract method to split the text into chunks.
        """
        pass

    def create_documents(self, texts: List[str]) -> List[str]:
        """
        Splits each text using the split_text method and returns all chunks.
        """
        documents: List[str] = []
        for text in texts:
            documents.extend(self.split_text(text))
        return documents

    def split_documents(self, documents: List[str]) -> List[str]:
        """
        Alias for create_documents.
        """
        return self.create_documents(documents)

    def join_docs(self, docs: List[str], separator: str) -> Optional[str]:
        """
        Joins document chunks using the given separator.
        Returns None if the result is empty.
        """
        joined = separator.join(docs).strip()
        return joined if joined else None

    def merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        Merges a list of text splits into chunks respecting the chunk_size and chunk_overlap.
        """
        docs: List[str] = []
        current_doc: List[str] = []
        total = 0
        for s in splits:
            s_len = len(s)
            if total + s_len >= self.chunk_size:
                if total > self.chunk_size:
                    print(f"Warning: Created a chunk of size {total}, which exceeds {self.chunk_size}")
                if current_doc:
                    merged = self.join_docs(current_doc, separator)
                    if merged is not None:
                        docs.append(merged)
                    # Remove elements from the beginning until conditions are met.
                    while current_doc and (total > self.chunk_overlap or (total + s_len > self.chunk_size and total > 0)):
                        removed = current_doc.pop(0)
                        total -= len(removed)
            current_doc.append(s)
            total += s_len
        merged = self.join_docs(current_doc, separator)
        if merged is not None:
            docs.append(merged)
        return docs

class RecursiveCharacterTextSplitter(TextSplitter):
    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 separators: Optional[List[str]] = None) -> None:
        super().__init__(chunk_size, chunk_overlap)
        # Use default separators if not provided.
        self.separators = separators if separators is not None else ['\n\n', '\n', '.', ',', '>', '<', ' ', '']

    def split_text(self, text: str) -> List[str]:
        """
        Splits the text into chunks using an appropriate separator.
        Handles long chunks recursively.
        """
        final_chunks: List[str] = []

        # Select appropriate separator.
        separator = self.separators[-1]  # default to last element (usually '')
        for sep in self.separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break

        # Split text using the chosen separator.
        if separator:
            splits = text.split(separator)
        else:
            # If separator is empty, split into individual characters.
            splits = list(text)

        good_splits: List[str] = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self.merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                # Recursively split the long segment.
                final_chunks.extend(self.split_text(s))
        if good_splits:
            merged = self.merge_splits(good_splits, separator)
            final_chunks.extend(merged)
        return final_chunks

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits the provided text into chunks using the RecursiveCharacterTextSplitter.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# Example usage for testing.
if __name__ == '__main__':
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "This is a sample text. It contains multiple sentences, "
        "and it should be split into smaller chunks. "
        "Each chunk will be processed accordingly. "
        "The purpose is to test the recursive text splitter implementation."
    )
    chunks = splitter.split_text(sample_text)
    for i, chunk in enumerate(chunks, start=1):
        print(f"Chunk {i}: {chunk}")
