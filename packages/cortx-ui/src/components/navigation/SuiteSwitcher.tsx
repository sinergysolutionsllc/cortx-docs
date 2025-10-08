'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../select';
import { cn } from '../../utils/cn';
import { suites } from '../../config/routes';
import { SuiteSwitcherProps } from '../../types/navigation';
import { useRouteBuilder } from '../../hooks/useNavigation';

/**
 * SuiteSwitcher - Dropdown component for switching between suites
 *
 * Features:
 * - Displays all available suites
 * - Shows current active suite
 * - Handles cross-domain navigation
 * - Indicates unavailable suites
 *
 * Usage:
 * ```tsx
 * <SuiteSwitcher
 *   currentDomain="fedsuite.ai"
 *   onSuiteChange={(domain) => console.log('Switching to:', domain)}
 * />
 * ```
 */
export function SuiteSwitcher({
  currentDomain,
  onSuiteChange,
  className,
}: SuiteSwitcherProps) {
  const { buildUrl } = useRouteBuilder();

  const handleSuiteChange = (value: string) => {
    const suite = suites.find(s => s.domain === value);
    if (!suite) return;

    // Don't allow switching to unavailable suites
    if (!suite.available) {
      return;
    }

    // Call callback if provided
    if (onSuiteChange) {
      onSuiteChange(suite.domain);
    }

    // Navigate to the suite
    const url = buildUrl(suite.domain, '/');
    window.location.href = url;
  };

  const currentSuite = suites.find(s => s.domain === currentDomain);

  return (
    <div className={cn('relative', className)}>
      <Select
        value={currentDomain}
        onValueChange={handleSuiteChange}
      >
        <SelectTrigger className="w-[180px] bg-background border-border">
          <SelectValue placeholder="Select Suite">
            {currentSuite ? (
              <div className="flex items-center gap-2">
                <span className="font-medium">{currentSuite.name}</span>
              </div>
            ) : (
              'Platform'
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {suites.map((suite) => (
            <SelectItem
              key={suite.domain}
              value={suite.domain}
              disabled={!suite.available}
              className={cn(
                'cursor-pointer',
                !suite.available && 'opacity-50 cursor-not-allowed'
              )}
            >
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{suite.label}</span>
                  {!suite.available && (
                    <span className="text-xs text-muted-foreground">
                      (Coming Soon)
                    </span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {suite.description}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

SuiteSwitcher.displayName = 'SuiteSwitcher';
