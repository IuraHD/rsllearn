import React from 'react';

interface TaskScreenSectionProps {
  title: string;
  maxWidthClass?: string;
  children: React.ReactNode;
}

export const TaskScreenSection: React.FC<TaskScreenSectionProps> = ({
  title,
  maxWidthClass = 'max-w-3xl',
  children,
}) => (
  <div className={`text-center w-full ${maxWidthClass} mx-auto animate-pop-in`}>
    <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-dark-100 mb-6 sm:mb-8 leading-tight break-words">
      {title}
    </h2>
    {children}
  </div>
);
