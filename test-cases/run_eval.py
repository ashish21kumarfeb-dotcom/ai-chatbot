import json
import requests
from pathlib import Path

CHAT_URL = "http://localhost:8000/chat"


def normalize(text: str) -> str:
    return (text or "").lower()


def call_chat_api(question: str) -> dict:
    payload = {"question": question, "session_id": "eval-session"}

    response = requests.post(CHAT_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def check_case(case: dict, answer: str) -> list[str]:
    failures = []
    answer_lc = normalize(answer)

    for item in case.get("must_contain", []):
        if normalize(item) not in answer_lc:
            failures.append(f"Missing required text: {item}")

    must_contain_any = case.get("must_contain_any", [])
    if must_contain_any:
        found_any = any(normalize(item) in answer_lc for item in must_contain_any)
        if not found_any:
            failures.append(f"None of these appeared in answer: {must_contain_any}")

    for item in case.get("must_not_contain", []):
        if normalize(item) in answer_lc:
            failures.append(f"Forbidden text appeared: {item}")

    min_answer_length = case.get("min_answer_length")
    if min_answer_length is not None:
        if len(answer.strip()) < min_answer_length:
            failures.append(
                f"Answer is too short. Expected at least {min_answer_length} characters."
            )

    must_not_equal_any = case.get("must_not_equal_any", [])
    normalized_answer_exact = " ".join(answer.strip().lower().split())

    for forbidden_exact in must_not_equal_any:
        normalized_forbidden = " ".join(str(forbidden_exact).strip().lower().split())
        if normalized_answer_exact == normalized_forbidden:
            failures.append(
                f"Answer exactly matched forbidden output: {forbidden_exact}"
            )

    if not answer.strip():
        failures.append("Answer is empty")

    return failures


def main():
    cases_path = Path(__file__).parent / "eval_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    total = len(cases)
    passed = 0
    failed = 0

    print("\n==============================")
    print("Running Local AI Eval Suite")
    print("==============================\n")

    for case in cases:
        print(f"CASE: {case['id']}")
        print(f"QUESTION: {case['question']}")

        try:
            result = call_chat_api(case["question"])
            answer = result.get("answer", "")

            failures = check_case(case, answer)

            print("\nANSWER:")
            print(answer)

            if failures:
                failed += 1
                print("\nSTATUS: FAILED")
                for failure in failures:
                    print(f"- {failure}")
            else:
                passed += 1
                print("\nSTATUS: PASSED")

            print("\n------------------------------\n")

        except Exception as ex:
            failed += 1
            print("\nSTATUS: ERROR")
            print(str(ex))
            print("\n------------------------------\n")

    print("==============================")
    print("Eval Summary")
    print("==============================")
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
