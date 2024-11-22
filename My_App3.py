import streamlit as st
import os, sqlite3
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Load the tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# Set pad_token_id to eos_token_id to avoid warnings
tokenizer.pad_token = tokenizer.eos_token

## Function to load the model and provide queries as response
def get_model_response(question, prompt):
    inputs = tokenizer(prompt[0] + question, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(inputs.input_ids, attention_mask=inputs.attention_mask, max_new_tokens=100, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

## Function to clean up the generated SQL query
def clean_sql_query(query):
    # Remove any unwanted tokens or fix common issues
    unwanted_tokens = ["[PAD]", "[unused0]", "[unused1]", "[CLS]", "[SEP]"]
    for token in unwanted_tokens:
        query = query.replace(token, "")
    # Ensure the query starts with a valid SQL command
    sql_commands = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    for command in sql_commands:
        if query.strip().upper().startswith(command):
            return query.strip()
    return ""

## Function to retrieve query from the database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"SQL error: {e}")
        rows = []
    conn.close()
    for row in rows:
        print(row)
    return rows

## Define your prompt
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The e-commerce database has two tables: ORDERS and PRODUCTS.

    The ORDERS table has the following columns:
    - Product_ID
    - ProductName
    - Category
    - Category_ID
    - OrderID
    - CustomerID
    - OrderStatus
    - ReturnEligible
    - ShippingDate

    The PRODUCTS table has the following columns:
    - Product_ID
    - ProductName
    - Merchant_ID
    - Cluster_ID
    - Cluster_Label
    - Category_ID
    - Category
    - Price
    - StockQuantity
    - Description
    - Rating

    For example,
    Example 1 - How many orders are there for the product with Product_ID 123?, 
    the SQL command will be: SELECT COUNT(*) FROM ORDERS WHERE Product_ID = 123;

    Example 2 - List all products in the 'Electronics' category, 
    the SQL command will be: SELECT * FROM PRODUCTS WHERE Category = 'Electronics';

    Example 3 - What is the average rating of products in the 'Home Appliances' category?, 
    the SQL command will be: SELECT AVG(Rating) FROM PRODUCTS WHERE Category = 'Home Appliances';

    Generate only the SQL query without any additional text.
    """
]

## Streamlit App
st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("App to Retrieve SQL Data")

question = st.text_input("Input: ", key="input")

submit = st.button("Ask the question")

if submit:
    response = get_model_response(question, prompt)
    response = clean_sql_query(response)
    if response:
        print("Generated SQL Query:", response)  # Add this line to inspect the query
        response = read_sql_query(response, "ecommerce.db")
        st.subheader("The Response is")
        for row in response:
            print(row)
            st.header(row)
    else:
        st.error("Failed to generate a valid SQL query.")