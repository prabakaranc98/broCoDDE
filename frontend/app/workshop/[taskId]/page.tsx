import { WorkshopView } from "@/components/workshop/WorkshopView";

interface Props {
    params: Promise<{ taskId: string }>;
}

export default async function WorkshopPage({ params }: Props) {
    const { taskId } = await params;
    return <WorkshopView taskId={taskId} />;
}
