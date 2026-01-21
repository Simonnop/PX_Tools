import requests

url = "http://127.0.0.1:10101/llm/ask_with_files"

with open("Investigation_of_Artificial_Intelligence_Vulnerability_in_Smart_Grids_A_Case_from_Solar_Energy_Forecasting.pdf", "rb") as f1, open("TS-Inverse_A_Gradient_Inversion_Attack_Tailored_for_Federated_Time_Series_Forecasting_Models.pdf", "rb") as f2:
    r = requests.post(
        url,
        data={"question": "what are the main ideas of these paper?"},
        files=[("files", f1), ("files", f2)],
        timeout=600,
    )
print(r.json()["data"]["answer"])