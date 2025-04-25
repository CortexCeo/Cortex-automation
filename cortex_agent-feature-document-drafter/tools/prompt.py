"""Prompts."""

from typing import Any, Dict

PROMPTS: Dict[str, Any] = {}

    # Few-shot examples with an input text and its corresponding final table.
FEW_SHOT_EXAMPLES_TABLE = """
    Example 1:
    Input Text:
    “The AI model was evaluated on multiple benchmarks, including accuracy, precision, recall, and F1-score. The accuracy of the model reached 92.5% on the ImageNet dataset, while the precision and recall were measured at 89.2% and 90.1%, respectively. The F1-score, which balances precision and recall, was calculated as 89.6%. The evaluation also included latency analysis, where the model inference time was recorded as 12.5 milliseconds per image. Energy consumption was another factor, with the model consuming 2.3 watts per inference.”
    Final Table:
    [
    {{
        "Evaluation Category": "Classification Metrics",
        "Metric / Description": "Accuracy",
        "Benchmark / Scenario": "ImageNet dataset",
        "Performance Result": "92.5%"
    }},
    {{
        "Evaluation Category": "Classification Metrics",
        "Metric / Description": "Precision",
        "Benchmark / Scenario": "ImageNet dataset",
        "Performance Result": "89.2%"
    }},
    {{
        "Evaluation Category": "Classification Metrics",
        "Metric / Description": "Recall",
        "Benchmark / Scenario": "ImageNet dataset",
        "Performance Result": "90.1%"
    }},
    {{
        "Evaluation Category": "Classification Metrics",
        "Metric / Description": "F1-score",
        "Benchmark / Scenario": "ImageNet dataset",
        "Performance Result": "89.6%"
    }},
    {{
        "Evaluation Category": "Latency Analysis",
        "Metric / Description": "Inference Time",
        "Benchmark / Scenario": "Per image processing",
        "Performance Result": "12.5 ms"
    }},
    {{
        "Evaluation Category": "Energy Consumption",
        "Metric / Description": "Power Usage",
        "Benchmark / Scenario": "Per inference",
        "Performance Result": "2.3 watts"
    }}
    ]
    
    Example 2:
    Input Text:
    “A recent workplace study assessed employee satisfaction, managerial effectiveness, and remote work productivity. The survey found that 78% of employees reported high satisfaction with flexible work hours. Additionally, managerial effectiveness was evaluated through 360-degree feedback, where 85% of employees rated their managers as supportive. The study also examined remote work productivity, finding that employees working remotely maintained 95% of their in-office efficiency. Overall, the study suggests that hybrid work models improve employee well-being while sustaining productivity.”

    Final Table:
    [
    {{
        "Evaluation Category": "Employee Satisfaction",
        "Metric / Description": "Percentage of employees satisfied with flexible work hours",
        "Benchmark / Scenario": "Workplace study survey",
        "Performance Result": "78% approval"
    }},
    {{
        "Evaluation Category": "Managerial Effectiveness",
        "Metric / Description": "360-degree feedback on managerial support",
        "Benchmark / Scenario": "Employee survey results",
        "Performance Result": "85% positive rating"
    }},
    {{
        "Evaluation Category": "Remote Work Productivity",
        "Metric / Description": "Productivity comparison between in-office and remote work",
        "Benchmark / Scenario": "Remote work efficiency assessment",
        "Performance Result": "95% productivity retention"
    }}
    ]
    """
# Prompts we will use
PROMPTS["table_composer"] = f"""
Role & Task:
You are an intelligent extraction assistant that converts unstructured text into a structured table in valid JSON format. Your task is to:
	1.	Identify relevant columns that can be used to group and categorize the extracted data.
	2.	Structure the extracted data into rows, ensuring that all objects (rows) share the same schema.
	3.	Dynamically determine column names based on the input text while maintaining consistency with previous examples.
 
 Instructions:
	Step 1: Decide column names that best represent the key groupings in the text.
	Step 2: Number of colmnns shuld not be more than 5.
	Step 3: Extract relevant details and assign them to the appropriate columns.
	Step 4: Ensure all rows follow the same schema with a valid JSON structure.
	Step 5: Number of rows should not be more than 10.
	Step 5: Validate the output to ensure consistency and correctness.
 
 
Few-shot examples:
{FEW_SHOT_EXAMPLES_TABLE}

Now, given the input below, generate the table.
Always validate the Final Table to ensure that all objects (rows) share the same keys.
Input Text: 
"{{input_text}}"

Final Table:
"""
 
PROMPTS["text_corpus_builder"] = """You are an advanced text corpus generator. Based on the following recent conversation history, generate a structured and contextually rich text corpus that aligns with the user’s intent. 

### Instructions:
- Prioritize the **most recent interactions** to ensure relevance.
- Extract key topics, metrics, benchmarks, and evaluations from the conversation.
- If tool responses are present, **integrate their results meaningfully** into the corpus.
- Ensure **logical flow** and avoid repetitive phrasing.
- Use a mix of **qualitative descriptions and quantitative insights**.
- Introduce **hypothetical scenarios, case studies, or industry references** where necessary.
- The corpus **must be at least 100 words long** and should support structured table extraction.
- **If the conversation is too short to generate at least 100 words, return `False`.**

---

### **Recent Conversation History:**
{recent_conversation_history}

---

### **User’s Intent:**
{user_intent}

---

### **Generated Text Corpus:**
(If the generated corpus contains 100+ words, provide the structured text. Otherwise, return `False`.)"""