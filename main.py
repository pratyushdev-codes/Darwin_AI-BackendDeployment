import json
import os
import numpy as np
import faiss
from typing import List, Dict, Any
import google.generativeai as genai
from dataclasses import dataclass
import pickle
import hashlib
from dotenv import load_dotenv


load_dotenv()

@dataclass
class KnowledgeItem:
    """Represents a piece of coding knowledge for the RAG system"""
    content: str
    category: str
    resource_link: str
    embedding: np.ndarray = None

class EmpathyRAGSystem:
    """RAG system for retrieving relevant coding best practices and explanations"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.embedding_model = 'models/embedding-001'
        
        
        self.dimension = 768 
        self.index = faiss.IndexFlatIP(self.dimension)  
        self.knowledge_base: List[KnowledgeItem] = []
        
    
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with coding best practices"""
        knowledge_items = [
            {
                "content": "List comprehensions in Python are more efficient than traditional for loops with append operations because they are optimized at the C level and don't require multiple function calls.",
                "category": "performance",
                "resource_link": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions"
            },
            {
                "content": "Meaningful variable names improve code readability and maintainability. Single-letter variables should be avoided except for short loops or mathematical contexts.",
                "category": "readability",
                "resource_link": "https://pep8.org/#naming-conventions"
            },
            {
                "content": "Comparing boolean values with == True or == False is redundant in Python. The truthiness of the value can be evaluated directly.",
                "category": "pythonic",
                "resource_link": "https://pep8.org/#programming-recommendations"
            },
            {
                "content": "Code reviews should focus on improvement rather than criticism. Constructive feedback helps team members learn and grow.",
                "category": "team_dynamics",
                "resource_link": "https://google.github.io/eng-practices/review/reviewer/comments.html"
            },
            {
                "content": "Performance optimizations should be considered when dealing with large datasets. Algorithm complexity matters for scalability.",
                "category": "performance",
                "resource_link": "https://wiki.python.org/moin/PythonSpeed/PerformanceTips"
            },
            {
                "content": "Filter operations in functional programming can be combined with map operations for cleaner, more readable code.",
                "category": "functional_programming",
                "resource_link": "https://docs.python.org/3/howto/functional.html"
            }
        ]
        
        for item_data in knowledge_items:
            
            embedding = self._get_embedding(item_data["content"])
            
            knowledge_item = KnowledgeItem(
                content=item_data["content"],
                category=item_data["category"],
                resource_link=item_data["resource_link"],
                embedding=embedding
            )
            
            self.knowledge_base.append(knowledge_item)
            
            # Add to FAISS index self.index.add(embedding.reshape(1, -1))
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Gemini embedding model"""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'], dtype=np.float32)
        except Exception as e:
            print(f"Error generating embedding: {e}")
           
            return np.zeros(self.dimension, dtype=np.float32)
    
    def retrieve_relevant_knowledge(self, query: str, k: int = 3) -> List[KnowledgeItem]:
        """Retrieve relevant knowledge items based on the query"""
        query_embedding = self._get_embedding(query)
        
       
        scores, indices = self.index.search(query_embedding.reshape(1, -1), k)
        
        relevant_items = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.knowledge_base) and scores[0][i] > 0.1: 
                relevant_items.append(self.knowledge_base[idx])
        
        return relevant_items

class EmpathethicCodeReviewer:
    """Main class for transforming critical code review comments into empathetic feedback"""
    
    def __init__(self, api_key: str):
        self.rag_system = EmpathyRAGSystem(api_key)
        self.model = self.rag_system.model
    
    def _determine_severity(self, comment: str) -> str:
        """Determine the severity/tone of the original comment"""
        harsh_indicators = ['bad', 'wrong', 'terrible', 'awful', 'stupid', 'inefficient']
        moderate_indicators = ['should', 'could', 'consider', 'might']
        
        comment_lower = comment.lower()
        
        if any(indicator in comment_lower for indicator in harsh_indicators):
            return "harsh"
        elif any(indicator in comment_lower for indicator in moderate_indicators):
            return "moderate"
        else:
            return "neutral"
    
    def _generate_empathetic_response(self, code_snippet: str, comment: str, severity: str, relevant_knowledge: List[KnowledgeItem]) -> Dict[str, str]:
        """Generate empathetic response using Gemini AI with RAG context"""
        
       
        context = "\n".join([f"- {item.content}" for item in relevant_knowledge])
        resource_links = [item.resource_link for item in relevant_knowledge]
        
        severity_guidance = {
            "harsh": "The original comment was quite direct. Please be extra gentle and encouraging in your response.",
            "moderate": "The original comment was moderately constructive. Maintain a supportive tone.",
            "neutral": "The original comment was neutral. Provide balanced, educational feedback."
        }
        
        prompt = f"""
You are an empathetic senior developer reviewing code. Transform the following critical comment into constructive, educational feedback.

Code Snippet:
```python
{code_snippet}
```

Original Comment: "{comment}"

Severity Context: {severity_guidance[severity]}

Relevant Knowledge Context:
{context}

Please provide:

1. **Positive Rephrasing**: Rewrite the comment to be encouraging and constructive while maintaining the technical accuracy. Start with something positive about the code.

2. **The 'Why'**: Explain the underlying software engineering principle or best practice. Make it educational and help the developer understand the reasoning.

3. **Suggested Improvement**: Provide a concrete code example that demonstrates the recommended fix. Make sure it's directly applicable to the given code snippet.

Format your response as JSON with keys: "positive_rephrasing", "the_why", "suggested_improvement", "code_example"

Be warm, encouraging, and educational. Focus on growth and learning rather than criticism.
"""

        try:
            response = self.model.generate_content(prompt)
            
      
            try:
                result = json.loads(response.text.strip())
            except json.JSONDecodeError:
 
                result = self._parse_fallback_response(response.text)
            
  
            if resource_links:
                result["resource_links"] = list(set(resource_links))
            
            return result
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "positive_rephrasing": "Thanks for sharing your code! There's an opportunity to improve this section.",
                "the_why": "Code improvements help with maintainability and performance.",
                "suggested_improvement": "Consider refactoring this section for better clarity.",
                "code_example": "# Improved version would go here",
                "resource_links": []
            }
    
    def _parse_fallback_response(self, response_text: str) -> Dict[str, str]:
        """Fallback parser for non-JSON responses"""
        result = {
            "positive_rephrasing": "",
            "the_why": "",
            "suggested_improvement": "",
            "code_example": "",
            "resource_links": []
        }
        
        # Simple text parsing logic
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'positive rephrasing' in line.lower():
                current_section = 'positive_rephrasing'
            elif 'why' in line.lower():
                current_section = 'the_why'
            elif 'suggested improvement' in line.lower() or 'improvement' in line.lower():
                current_section = 'suggested_improvement'
            elif line.startswith('```'):
                current_section = 'code_example' if current_section != 'code_example' else None
            elif current_section and line:
                if current_section in result:
                    result[current_section] += line + " "
        
        return result
    
    def process_review(self, input_data: Dict[str, Any]) -> str:
        """Process the code review and generate empathetic feedback report"""
        code_snippet = input_data.get("code_snippet", "")
        review_comments = input_data.get("review_comments", [])
        
        if not code_snippet or not review_comments:
            return "Error: Missing code snippet or review comments."
        
        markdown_report = "# Empathetic Code Review Report\n\n"
        markdown_report += f"## Code Under Review\n\n```python\n{code_snippet}\n```\n\n"
        
        all_feedback = []
        
        for i, comment in enumerate(review_comments, 1):
          
            relevant_knowledge = self.rag_system.retrieve_relevant_knowledge(comment)
            
          
            severity = self._determine_severity(comment)
            
          
            response = self._generate_empathetic_response(
                code_snippet, comment, severity, relevant_knowledge
            )
            
   
            section = f"### Analysis of Comment {i}: \"{comment}\"\n\n"
            section += f"**Positive Rephrasing:** {response.get('positive_rephrasing', '')}\n\n"
            section += f"**The 'Why':** {response.get('the_why', '')}\n\n"
            section += f"**Suggested Improvement:**\n{response.get('suggested_improvement', '')}\n\n"
            
            if response.get('code_example'):
                section += f"```python\n{response.get('code_example', '')}\n```\n\n"
            
            if response.get('resource_links'):
                section += "**Additional Resources:**\n"
                for link in response.get('resource_links', []):
                    section += f"- [{link}]({link})\n"
                section += "\n"
            
            section += "---\n\n"
            markdown_report += section
            all_feedback.append(response)
        
 
        summary = self._generate_holistic_summary(code_snippet, review_comments, all_feedback)
        markdown_report += f"## Overall Summary\n\n{summary}\n\n"
        markdown_report += "*Remember: Every piece of feedback is an opportunity to grow. Keep coding and keep learning!* 🚀"
        
        return markdown_report
    
    def _generate_holistic_summary(self, code_snippet: str, comments: List[str], feedback: List[Dict]) -> str:
        """Generate an encouraging summary of all feedback"""
        prompt = f"""
Based on the code review feedback provided, generate a brief, encouraging summary that:
1. Acknowledges the positive aspects of the original code
2. Highlights the main learning opportunities
3. Motivates the developer to continue improving
4. Keeps a warm, supportive tone

Original code had {len(comments)} review points. Focus on growth and learning.
Keep the summary to 2-3 sentences maximum.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Great work on submitting your code for review! The feedback provided will help you write even better code in the future. Keep up the excellent learning attitude!"

def main():
    """Main function to demonstrate the empathetic code reviewer"""
    

    API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not API_KEY or API_KEY == "your_actual_gemini_api_key_here":
        print(" GEMINI_API_KEY not found!")
        print("\nTo fix this:")
        print("1. Create a .env file in the Backend directory")
        print("2. Add your Gemini API key: GEMINI_API_KEY=your_actual_key_here")
        print("3. Get your API key from: https://makersuite.google.com/app/apikey")
        print("\nOr set it as an environment variable:")
        print("export GEMINI_API_KEY=your_actual_key_here")
        return
    
    # Example input
    sample_input = {
        "code_snippet": "def get_active_users(users):\n    results = []\n    for u in users:\n        if u.is_active == True and u.profile_complete == True:\n            results.append(u)\n    return results",
        "review_comments": [
            "This is inefficient. Don't loop twice conceptually.",
            "Variable 'u' is a bad name.",
            "Boolean comparison '== True' is redundant."
        ]
    }
    
   
    reviewer = EmpathethicCodeReviewer(API_KEY)
    
    
    print("Processing code review...")
    result = reviewer.process_review(sample_input)
    
    
    print("\n" + "="*80)
    print("EMPATHETIC CODE REVIEW REPORT")
    print("="*80)
    print(result)
    

    with open("empathetic_review_report.md", "w") as f:
        f.write(result)
    
    print("\n" + "="*80)
    print("Report saved to 'empathetic_review_report.md'")

if __name__ == "__main__":
    main()