import { Button } from "@/components/ui/button";
import { AssignmentsDataType } from "@/fakedata/assignments-reponse";

export default function CodeResults({ data }: { data: AssignmentsDataType }) {
    const handleCheckCode = () => {
        document.getElementById("feedback")!.classList.toggle("hidden");
    }

    return (
        <div>
            <Button onClick={handleCheckCode} className="w-full mt-2">Check Code</Button>

            <div id="feedback" className="display flex flex-1 flex-col">
                <div className="p-2 gap-2">
                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Feedback:</p>
                        <p>Score: {data.response.data.projected_result.projected_score}</p>
                        <p>{data.response.data.projected_result.feedback.summary}</p>
                    </pre>

                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Test Cases:</p>
                        <p>{JSON.stringify(data.response.data.projected_result.test_results, null, 2)}</p>
                    </pre>

                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Constraints Violations:</p>
                        <p>{JSON.stringify(data.response.data.projected_result.constraint_result.warnings, null, 2)}</p>
                    </pre>
                </div>
            </div>
        </div>
    )
}