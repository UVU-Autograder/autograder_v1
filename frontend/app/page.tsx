import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Welcome</CardTitle>
          <CardDescription>
            Select how you would like to continue
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button asChild size="lg" className="w-full">
            <Link href="/staff">Login as Instructor</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full">
            <Link href="/sandbox">Login as Student</Link>
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
