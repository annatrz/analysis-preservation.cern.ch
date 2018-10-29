import React from "react";
import PropTypes from "prop-types";
import _ from "lodash";

import { Box } from "grommet";

let ItemBrief = function(props) {
  const { index, item, label } = props;

  let preview = [];

  if (Array.isArray(label)) {
    label.map(prop => {
      preview.push(
        `${prop.title}${prop.separator || ":"} ${_.get(item, prop.path) || "-"}`
      );
    });
  } else {
    preview = label;
  }

  return (
    <Box direction="row" justify="between">
      {preview}
    </Box>
  );
};

ItemBrief.propTypes = {
  hasRemove: PropTypes.bool,
  hasMoveDown: PropTypes.bool,
  hasMoveUp: PropTypes.bool,
  onDropIndexClick: PropTypes.func,
  onReorderClick: PropTypes.func,
  index: PropTypes.string,
  item: PropTypes.object,
  label: PropTypes.string
};

export default ItemBrief;
