export function formatQuestion(question: string): string {
    return `Q: ${question}`;
}

export function formatAnswer(answer: string): string {
    return `A: ${answer}`;
}

export function validateInput(input: string): boolean {
    return input.trim().length > 0;
}

export function loadTopics(): string[] {
    // Replace with your actual implementation
    return ["Example Topic 1", "Example Topic 2"];
}

export function loadQuestions(): string[] {
    // Replace with your actual implementation
    return ["Example Question 1", "Example Question 2"];
}