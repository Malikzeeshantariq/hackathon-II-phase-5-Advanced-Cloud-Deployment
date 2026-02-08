/** Chat page for the Todo AI Chatbot. */
"use client";

import ChatPanel from "@/components/ChatPanel";

const ChatPage = () => {
  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Task Assistant</h1>
        <p className="text-gray-600 mt-1">
          Manage your tasks using natural language. Ask me to create, list,
          complete, delete, or update tasks.
        </p>
      </div>

      {/* Chat Panel */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="h-[500px] flex flex-col">
          <ChatPanel />
        </div>
      </div>

      {/* Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-100 rounded-lg p-4">
        <h3 className="font-medium text-blue-800">
          Tips for using the AI Assistant:
        </h3>
        <ul className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-blue-700">
          <li className="flex items-start">
            <span className="mr-2">&bull;</span>
            <span>Add tasks: &quot;Add a task to buy groceries&quot;</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">&bull;</span>
            <span>
              List tasks: &quot;Show my tasks&quot; or &quot;What tasks are
              pending?&quot;
            </span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">&bull;</span>
            <span>
              Complete tasks: &quot;Mark &apos;buy groceries&apos; as done&quot;
            </span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">&bull;</span>
            <span>Delete tasks: &quot;Delete the groceries task&quot;</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default ChatPage;
