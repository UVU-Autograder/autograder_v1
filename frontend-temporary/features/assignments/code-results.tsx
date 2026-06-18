import { Button } from "@/components/ui/button";
import { AssignmentsDataType } from "@/fakedata/assignments-reponse";

export default function CodeResults({ data }: { data: AssignmentsDataType }) {
    const handleCheckCode = () => {
        document.getElementById("check-code")!.classList.toggle("hidden");
    }
    const handleFeedback = () => {
        document.getElementById("feedback")!.classList.toggle("hidden");
    }
    // To handle constraints
    const warnings =  data.response.data.projected_result.constraint_result.warnings;

    // Score calculation in percentage 
    const percent = Math.round((data.response.data.projected_result.projected_score / data.response.data.projected_result.max_score) * 100);

    return (
        <div>
            <Button onClick={handleCheckCode} className="w-full mt-2 bg-gradient-to-r from-gray-800 to-gray-500
            hover:from-black-800 hover:to-indigo-600 text-white text-lg font-semibold px-6 py-3 rounded-lg">
            Check Code</Button>

            {/* <div id="score" className="display flex flex-1 flex-col">
                <pre className="text-wrap">
                    <p className="font-bold text-lg mb-2">Score:</p>
                    <p>{data.response.data.projected_result.projected_score} / {data.response.data.projected_result.max_score}</p>
                </pre>

                <div className="w-full bg-slate-200 rounded-full h-2 mt-3">
                    <div
                    className="h-2 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg"
                    style={{ width: `${percent}%` }}
                    />
                </div>

            </div> */}

  
            <div id="check-code" className="display flex flex-1 flex-col">
                <pre className="text-wrap">                  
                    <p className="font-bold text-lg mb-2">Score:</p>
                    <p>{data.response.data.projected_result.projected_score} / {data.response.data.projected_result.max_score}</p>
                    <div className="w-full bg-slate-200 rounded-full h-2 mt-3">
                        <div
                        className="h-2 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg"
                        style={{ width: `${percent}%` }}
                        />
                    </div>

                    <p className="font-bold text-lg mb-2">Test Cases:</p>
                    <div>
                        {data.response.data.projected_result.test_results.map((test: any, index: number) => (
                            <div
                            key={test.test_key}
                            className={`p-3 mb-2 rounded-lg border ${
                                test.passed
                                ? "border-green-300 bg-green-50"
                                : "border-red-300 bg-red-50"
                            }`}
                            >
                            {/*Header */}
                            <div className="flex justify-between items-center mb-2">
                                <p className="font-semibold">
                                    Test Case #{index + 1}
                                </p>
                                <p className="font-small">{test.description}</p>

                            <span
                            className={`text-sm font-bold ${
                            test.passed ? "text-green-600" : "text-red-600"
                            }`}                       >
                            {test.passed ? "✅ Passed" : "❌ Failed"}
                            </span>
                    </div>

                    {/* INPUT / OUTPUT (simulated from backend data) */}
                    <div className="text-sm space-y-1 text-slate-700">
                        <p>
                            <span className="font-medium">Input:</span>{" "}
                            {test.stdout || "N/A"}
                        </p>

                        <p>
                            <span className="font-medium">Expected Output:</span>{" "}
                            {test.test_key === "test_sorted_asc"
                                ? "[1, 2, 5, 8, 9]" // example override OR backend field later
                                : "See assertion"}
                        </p>
                    </div>

                    {/* PERFORMANCE INFO IF Backend Provides It. if not, we'll delete this block */}
                    <div className="mt-2 text-xs text-slate-500 flex gap-3">
                        <span>⚡ 0.02s</span>
                        <span>•</span>
                        <span>4800 KB</span>
                    </div>

                    {/* ERROR (if failed) */}
                    {test.stderr && (
                        <pre className="mt-2 text-xs text-red-600 whitespace-pre-wrap">
                        {test.stderr}
                        </pre>
                    )}
                    </div>
                    ))}
                    </div>                       
                </pre>

                <br />

                <pre className="text-wrap">
                    <p className="font-bold text-lg">Constraints Violations:</p>
                    <div className="mt-4 space-y-3">
                        {warnings.map((w: any, index: number) => (
                            <div
                                key={index}
                                className= "border-l-4 border-red-500 bg-red-50 rounded-md p-4"
                            >
                            <div className="flex justify-between">
                                <p className= "text-red-700 font-semibold">
                                    ⚠ Constraint Warning
                                </p>

                                <span className="text-xs text-black-500">
                                    Line {w.line}, Column {w.column}
                                </span>
                            </div>
                            <p className="text-sm text-red-500 mt-2">
                                {w.message}
                            </p>

                            {w.concept && (
                                <p className="text-xs text-black-500 mt-1">
                                    Concept: {w.concept}
                                </p>
                            )}                        
                    </div>
                        ))}
                    </div>
                </pre>
            </div>

            <br />

            <Button onClick={handleFeedback} className="w-full mt-2 bg-gradient-to-r from-purple-400 to-pink-500
            hover:from-purple-600 hover:to-pink-600 text-white text-lg font-semibold px-6 py-3 rounded-lg">
            View AI Feedback</Button>
            <div id="feedback" className="display flex flex-1 flex-col">
                <pre className="text-wrap">
                    <p className="font-bold text-lg">Feedback:</p>
                    <p>{data.response.data.projected_result.feedback.summary}</p>
                </pre>
            </div>
        </div>        
    )
}