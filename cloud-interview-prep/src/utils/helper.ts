export function formatQuestion(question: string): string {
    return `Q: ${question}`;
}

export function formatAnswer(answer: string): string {
    return `A: ${answer}`;
}

export function validateInput(input: string): boolean {
    return input.trim().length > 0;
}