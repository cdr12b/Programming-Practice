// This is the entry point of the application for the cloud interview preparation tool.

import { loadTopics, loadQuestions } from './utils/helper';

const main = async () => {
    const topics = await loadTopics();
    const questions = await loadQuestions();

    console.log("Welcome to the Cloud System Engineer Interview Preparation Tool!");
    console.log("Here are the topics you can study:");
    topics.forEach(topic => console.log(`- ${topic}`));

    console.log("\nPotential interview questions:");
    questions.forEach(question => console.log(`- ${question}`));
};

main().catch(error => {
    console.error("An error occurred:", error);
});