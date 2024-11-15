clc
clear all
% Read the image 
image = imread('map.png');
% Threshold the image 
threshold = 128;  
binary_image = image > threshold; 

% Ensure the binary image is 2D (grayscale)
if ndims(binary_image) > 2
    binary_image = uint8(binary_image) * 255; 
    binary_image = rgb2gray(binary_image); 
end

% Find boundaries of the shapes, excluding holes
boundaries = bwboundaries(binary_image, 4, 'noholes'); 

% Calculate the lengths of each boundary
boundary_lengths = cellfun('length', boundaries);

% Find the longest boundary (assumed to be the outermost one)
[~, max_length_index] = max(boundary_lengths);

% Exclude the longest boundary
boundaries(max_length_index) = [];

% Preallocate polyshape array (adjust size if needed)
pgon = repmat(polyshape, 1, length(boundaries)); 
A = [];

for i = 1:length(boundaries)
    verx = boundaries{i};
    pgon(i) = polyshape(verx);
    A(i) = area(pgon(i));
end

% Loop to find min/max points and replace original vertices
for i = 1:length(boundaries)
    if length(pgon(i).Vertices(:, 1)) > 6 
        % Find min/max X and their paired Y coordinates
        [minX, minXIndex] = min(pgon(i).Vertices(:, 1)); 
        minYPairedWithMinX = pgon(i).Vertices(minXIndex, 2);
        [maxX, maxXIndex] = max(pgon(i).Vertices(:, 1));
        maxYPairedWithMaxX = pgon(i).Vertices(maxXIndex, 2);

        % Find min/max Y and their paired X coordinates
        [minY, minYIndex] = min(pgon(i).Vertices(:, 2));
        minXPairedWithMinY = pgon(i).Vertices(minYIndex, 1);
        [maxY, maxYIndex] = max(pgon(i).Vertices(:, 2));
        maxXPairedWithMaxY = pgon(i).Vertices(maxYIndex, 1);

        % Create a new polyshape with ONLY the min/max points
        pgon(i) = polyshape([minX minYPairedWithMinX; minXPairedWithMinY minY; maxX maxYPairedWithMaxX; maxXPairedWithMaxY maxY]);
    end
end

% Plot the polygons with specified style
plot(pgon, 'FaceColor', 'none', 'EdgeColor', 'k', 'LineWidth', 1); 

all_points = [];

% --- Add points to each shape ---
for i = 1:length(pgon)
    x = pgon(i).Vertices(:,1);
    y = pgon(i).Vertices(:,2);

    xmin = min(x); 
    xmax = max(x);
    ymin = min(y); 
    ymax = max(y);

    % Calculate the spacing of the points
    x_spacing = 7.18; 
    y_spacing = 10.77;

    % Create a grid of points with margins (half the spacing)
    x_margin = x_spacing/2;
    y_margin = y_spacing/2;

    % Adjust margins to ensure they don't exceed shape dimensions
    x_margin = min(x_margin, (xmax - xmin) / 4);
    y_margin = min(y_margin, (ymax - ymin) / 4);

    [X, Y] = meshgrid(xmin + x_margin : x_spacing : xmax - x_margin, ...
                     ymin + y_margin : y_spacing : ymax - y_margin); 

    % Check which points fall inside the polygon
    valid_points = inpolygon(X(:), Y(:), x, y);

    % Extract the valid x and y coordinates
    x_points = X(valid_points);
    y_points = Y(valid_points);
    points = [x_points(:), y_points(:)];  % Combine x and y into a two-column array
    all_points = [all_points; points];   % Append to the main array
    disp(all_points);
    
    % --- Export all_points to a .csv file ---

    filename = 'coordinates.csv';
    writematrix(all_points, filename);

    disp(['Point coordinates exported to ', filename]);

    % Plot the modified polygons with hatching
    plot(x_points, y_points, 'ro', 'MarkerSize', 3, 'MarkerFaceColor', 'r');
    plot(pgon, 'FaceColor', 'none', 'EdgeColor', 'k', 'LineWidth', 1); 
    hold on;

end
