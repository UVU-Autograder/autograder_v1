export type RunProfile = 'PERFECT' | 'PARTIAL' | 'FAIL';

export const MOCK_COURSES = [
  { id: 'cs1400', title: 'Computer Science I', term: 'Fall 2026' },
  { id: 'cs1410', title: 'Computer Science II', term: 'Fall 2026' },
];

export const MOCK_ASSIGNMENTS = {
  cs1400: [
    { 
      id: 'simple-python-functions', 
      title: 'Simple Python Functions', 
      sandbox_enabled: true,
      rubric: [
        { key: 'add_numbers', points: 10, pytest_marker: 'ag_add_numbers', item_type: 'pytest' },
        { key: 'multiply_numbers', points: 10, pytest_marker: 'ag_multiply_numbers', item_type: 'pytest' },
      ]
    },
  ],
  cs1410: [
    { 
      id: 'lab-1-image-processing', 
      title: 'Lab 1: Image Processing', 
      sandbox_enabled: true,
      rubric: [
        { key: 'part1_files', points: 20, pytest_marker: 'ag_part1_files', item_type: 'pytest' },
        { key: 'grayscale_conv', points: 30, pytest_marker: 'ag_grayscale_conv', item_type: 'pytest' },
      ]
    },
  ],
};

export const RESULT_PROFILES: Record<RunProfile, any> = {
  PERFECT: {
    projected_score: 100,
    test_summaries: [
      { key: 'all', status: 'passed', message: 'All tests passed perfectly!' }
    ],
    sanitized_feedback: 'Excellent work. Your implementation is optimal and follows all constraints.',
  },
  PARTIAL: {
    projected_score: 86,
    test_summaries: [
      { key: 'core', status: 'passed', message: 'Core logic is correct.' },
      { key: 'edge_case', status: 'failed', message: 'Failed on empty input handling.' },
    ],
    sanitized_feedback: 'Good start, but you missed a few edge cases. Check your handling of null inputs.',
  },
  FAIL: {
    projected_score: 30,
    test_summaries: [
      { key: 'security', status: 'blocked', message: 'Hard-block: Use of forbidden library detected.' },
      { key: 'logic', status: 'failed', message: 'Logic error in main loop.' },
    ],
    sanitized_feedback: 'Your submission uses forbidden libraries. Please refer to the allowed concepts list.',
  },
};

export function getProfileFromFilename(filename: string): RunProfile {
  if (filename.toLowerCase().includes('perfect')) return 'PERFECT';
  if (filename.toLowerCase().includes('fail')) return 'FAIL';
  return 'PARTIAL';
}
